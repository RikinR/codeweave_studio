"""Resolve call chains for a symbol name within a repository.

Read-only traversal over persisted :class:`FunctionCallModel` rows. Does not
modify graph construction in :mod:`application.graph.build_graph`.
"""

from __future__ import annotations

from collections import deque
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from application.graph.build_graph import NODE_FUNCTION, NODE_METHOD, node_id
from application.graph.node_detail import get_call_refs
from infrastructure.db.models.file_model import FileModel
from infrastructure.db.models.function_calls_model import FunctionCallModel
from infrastructure.db.models.function_model import FunctionModel
from infrastructure.db.models.repository_model import RepositoryModel


def find_functions_by_name(
    session: Session,
    repository_id: UUID,
    symbol_name: str,
) -> list[FunctionModel]:
    """Return all functions/methods in the repository matching ``symbol_name``."""
    return (
        session.query(FunctionModel)
        .join(FileModel, FunctionModel.file_id == FileModel.id)
        .filter(FileModel.repository_id == repository_id, FunctionModel.name == symbol_name)
        .options(joinedload(FunctionModel.file).joinedload(FileModel.repository))
        .all()
    )


def _chain_step(fn: FunctionModel, *, direction: str) -> dict:
    node_type = NODE_METHOD if fn.class_id else NODE_FUNCTION
    repo = fn.file.repository if fn.file else None
    file_path = fn.file.file_path if fn.file else None
    if repo and file_path and repo.root_path:
        from application.ingestion.path_utils import relative_to_repo

        file_path = relative_to_repo(file_path, repo.root_path, repo.name)
    return {
        'node_id': node_id(node_type, fn.id),
        'name': fn.name,
        'file_path': file_path,
        'function_id': str(fn.id),
        'direction': direction,
    }


def _normalize_path(path: str) -> str:
    return path.replace('\\', '/').lstrip('/')


def _function_matches_file(fn: FunctionModel, file_path: str | None) -> bool:
    if not file_path or fn.file is None:
        return True
    repo = fn.file.repository
    display = fn.file.file_path
    if repo and repo.root_path:
        from application.ingestion.path_utils import relative_to_repo

        display = relative_to_repo(display, repo.root_path, repo.name)
    normalized = _normalize_path(file_path)
    display_norm = _normalize_path(display)
    return display_norm == normalized or display_norm.endswith('/' + normalized)


def build_call_chain(
    session: Session,
    repository_id: UUID,
    symbol_name: str,
    *,
    file_path: str | None = None,
    max_depth: int = 8,
    max_nodes: int = 64,
) -> dict:
    """Build upstream and downstream call chains starting at ``symbol_name``.

    Returns roots (matching symbols), ``upstream`` / ``downstream`` edge lists,
    and ``unresolved`` when the symbol is missing.
    """
    repo = session.get(RepositoryModel, repository_id)
    if repo is None:
        return {'repository_id': str(repository_id), 'symbol_name': symbol_name, 'roots': [], 'upstream': [], 'downstream': [], 'unresolved': True}

    roots = find_functions_by_name(session, repository_id, symbol_name)
    if file_path:
        scoped = [fn for fn in roots if _function_matches_file(fn, file_path)]
        if scoped:
            roots = scoped
    if not roots:
        return {
            'repository_id': str(repository_id),
            'symbol_name': symbol_name,
            'file_path': file_path,
            'roots': [],
            'upstream': [],
            'downstream': [],
            'unresolved': True,
            'ambiguous': False,
        }
    ambiguous = file_path is None and len(roots) > 1

    root_ids = {fn.id for fn in roots}
    upstream: list[dict] = []
    downstream: list[dict] = []

    def _walk(start: FunctionModel, *, incoming: bool) -> None:
        visited: set[UUID] = set()
        queue: deque[tuple[FunctionModel, int]] = deque([(start, 0)])
        edges: list[dict] = upstream if incoming else downstream
        while queue and len(visited) < max_nodes:
            fn, depth = queue.popleft()
            if fn.id in visited or depth >= max_depth:
                continue
            visited.add(fn.id)
            refs = get_call_refs(session, fn, repo=repo, incoming=incoming)
            for ref in refs:
                other_id = UUID(ref['node_id'].split(':', 1)[1])
                other = session.get(FunctionModel, other_id)
                if other is None:
                    continue
                edges.append(
                    {
                        'from': _chain_step(fn, direction='center' if fn.id in root_ids else ('upstream' if incoming else 'downstream')),
                        'to': _chain_step(other, direction='upstream' if incoming else 'downstream'),
                        'depth': depth + 1,
                    }
                )
                if other.id not in visited:
                    queue.append((other, depth + 1))

    for root in roots:
        _walk(root, incoming=True)
        _walk(root, incoming=False)

    return {
        'repository_id': str(repository_id),
        'symbol_name': symbol_name,
        'file_path': file_path,
        'roots': [_chain_step(fn, direction='root') for fn in roots],
        'upstream': upstream,
        'downstream': downstream,
        'unresolved': False,
        'ambiguous': ambiguous,
    }
