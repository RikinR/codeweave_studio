"""Assemble agent-facing context bundles from repository intelligence data.

Combines semantic retrieval, architecture graph summaries, call chains, and
node metadata without exposing FAISS or ORM details to callers.
"""

from __future__ import annotations

from collections import Counter
from uuid import UUID

from sqlalchemy.orm import Session

from application.graph.build_graph import (
    NODE_FUNCTION,
    NODE_METHOD,
    build_architecture_graph,
    build_hierarchy,
)
from application.graph.call_chain import build_call_chain
from application.graph.node_detail import get_node_detail
from application.ingestion.description_extract import is_generic_description
from application.ingestion.language_capabilities import supports_call_graph
from application.retrieval.retrieve_chunks import retrieve_chunks
from infrastructure.db.models.function_model import FunctionModel
from infrastructure.db.models.repository_model import RepositoryModel


def _architecture_summary(session: Session, repository_id: UUID) -> dict:
    graph = build_architecture_graph(session, repository_id)
    hierarchy = build_hierarchy(session, repository_id)
    type_counts = Counter(n.get('type') for n in graph.get('nodes') or [])
    call_edges = [e for e in graph.get('edges') or [] if e.get('kind') == 'calls']
    return {
        'repository_id': str(repository_id),
        'root_id': graph.get('root_id'),
        'node_counts': dict(type_counts),
        'call_edge_count': len(call_edges),
        'hierarchy_root_id': hierarchy.get('root_id'),
        'total_nodes': len(graph.get('nodes') or []),
        'total_edges': len(graph.get('edges') or []),
    }


def _entry_points(session: Session, repository_id: UUID, *, limit: int = 20) -> list[dict]:
    """Functions with no recorded incoming calls (approximate entry points)."""
    from infrastructure.db.models.file_model import FileModel
    from infrastructure.db.models.function_calls_model import FunctionCallModel

    fns = (
        session.query(FunctionModel)
        .join(FileModel, FunctionModel.file_id == FileModel.id)
        .filter(FileModel.repository_id == repository_id)
        .all()
    )
    if not fns:
        return []
    fn_ids = [fn.id for fn in fns]
    with_incoming = {
        row.callee_function_id
        for row in session.query(FunctionCallModel.callee_function_id)
        .filter(FunctionCallModel.callee_function_id.in_(fn_ids))
        .distinct()
    }
    entries = []
    preferred_names = {'main', '__init__', 'run', 'handler', 'execute', 'start'}
    for fn in fns:
        if fn.id in with_incoming and fn.name not in preferred_names:
            continue
        from application.graph.build_graph import NODE_FUNCTION, NODE_METHOD, node_id

        ntype = NODE_METHOD if fn.class_id else NODE_FUNCTION
        entries.append(
            {
                'node_id': node_id(ntype, fn.id),
                'name': fn.name,
                'function_id': str(fn.id),
                'preferred': fn.name in preferred_names,
            }
        )
    entries.sort(key=lambda e: (not e['preferred'], e['name']))
    return entries[:limit]


def _dependencies_from_graph(graph: dict, seed_node_ids: set[str]) -> list[dict]:
    """Outgoing ``calls`` edges from semantically matched functions."""
    deps: list[dict] = []
    seen: set[str] = set()
    for edge in graph.get('edges') or []:
        if edge.get('kind') != 'calls':
            continue
        source = edge.get('source')
        if source not in seed_node_ids:
            continue
        target = edge.get('target')
        if not target or target in seen:
            continue
        seen.add(target)
        deps.append({'source': source, 'target': target, 'kind': 'calls'})
    return deps


def build_context_package(
    session: Session,
    *,
    repository_id: UUID,
    goal: str,
    top_k: int = 12,
    chain_depth: int = 6,
) -> dict:
    """Build the primary agent context bundle for a repository and goal."""
    repo = session.get(RepositoryModel, repository_id)
    if repo is None:
        raise ValueError(f'Repository not found: {repository_id}')

    hits = retrieve_chunks(session, repository_id, goal, top_k=top_k)
    graph = build_architecture_graph(session, repository_id)

    affected_files: list[str] = []
    affected_functions: list[dict] = []
    seed_node_ids: set[str] = set()
    seen_paths: set[str] = set()
    seen_fn: set[str] = set()

    for ctx in hits:
        path = ctx.get('file_path')
        if path and path not in seen_paths:
            seen_paths.add(path)
            affected_files.append(path)
        fn_id = ctx.get('function_id')
        fn_name = ctx.get('function_name')
        graph_ok = bool(ctx.get('call_graph_available'))
        if fn_id and fn_id not in seen_fn:
            seen_fn.add(fn_id)
            ntype = NODE_METHOD if ctx.get('class_id') else NODE_FUNCTION
            nid = f'{ntype}:{fn_id}'
            if graph_ok:
                seed_node_ids.add(nid)
            affected_functions.append(
                {
                    'function_id': fn_id,
                    'function_name': fn_name,
                    'file_path': path,
                    'node_id': nid,
                    'score': ctx.get('score'),
                    'chunk_id': ctx.get('chunk_id'),
                    'intelligence_tier': ctx.get('intelligence_tier'),
                    'call_graph_available': graph_ok,
                    'indexing_notice': ctx.get('indexing_notice'),
                    'chunk_strategy': ctx.get('chunk_strategy'),
                }
            )

    call_chains: list[dict] = []
    chain_symbols = list({
        f['function_name']
        for f in affected_functions
        if f.get('function_name') and f.get('call_graph_available')
    })[:5]
    for symbol in chain_symbols:
        call_chains.append(
            build_call_chain(session, repository_id, symbol, max_depth=chain_depth)
        )

    context_gaps: list[str] = []
    if not hits:
        context_gaps.append('No semantic matches for goal; consider broader indexing or rephrasing.')
    text_only = [h for h in hits if not h.get('call_graph_available')]
    if text_only:
        context_gaps.append(
            f'{len(text_only)} retrieval hit(s) are text-indexed only (search works; call graph does not).'
        )
    low_conf = [h for h in hits if (h.get('score') or 0) < 0.25]
    if low_conf:
        context_gaps.append(f'{len(low_conf)} retrieval hit(s) have low similarity scores.')
    for fn_info in affected_functions[:8]:
        if not fn_info.get('call_graph_available'):
            continue
        detail = get_node_detail(session, fn_info['node_id'])
        if detail is None:
            context_gaps.append(f"Could not load detail for {fn_info['node_id']}.")
            continue
        if is_generic_description(detail.get('description')):
            context_gaps.append(f"Generic or missing description for {fn_info.get('function_name')} in {fn_info.get('file_path')}.")

    full_tier_hits = sum(1 for h in hits if supports_call_graph(h.get('intelligence_tier', '')))

    return {
        'repository_id': str(repository_id),
        'goal': goal,
        'architecture_summary': _architecture_summary(session, repository_id),
        'affected_files': affected_files,
        'affected_functions': affected_functions,
        'call_chains': call_chains,
        'entry_points': _entry_points(session, repository_id),
        'dependencies': _dependencies_from_graph(graph, seed_node_ids),
        'context_gaps': context_gaps,
        'retrieval_hits': hits,
        'intelligence_summary': {
            'full_tier_hits': full_tier_hits,
            'text_only_hits': len(text_only),
            'call_chains_built': len(call_chains),
        },
    }
