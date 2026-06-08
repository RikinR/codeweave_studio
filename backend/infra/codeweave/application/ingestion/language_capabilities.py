from __future__ import annotations

"""Language capability tiers for repository intelligence.

Single source of truth for what agents and the editor can expect per language:
semantic AST chunks, call graph, or text-only retrieval.
"""

from enum import StrEnum

from infrastructure.parser.language_specs import LANGUAGE_REGISTRY, supports_semantic_chunking


class IntelligenceTier(StrEnum):
    """Depth of code intelligence available for an indexed file or chunk."""

    FULL = 'full'
    """AST semantic chunks with reliable function boundaries and call graph."""
    PARSE = 'parse'
    """Tree-sitter parse succeeded but no semantic function extraction."""
    TEXT = 'text'
    """Plain or structural text chunks only (still searchable)."""
    UNKNOWN = 'unknown'


# Tree-sitter language ids with non-empty function queries in LANGUAGE_REGISTRY.
TIER_FULL_LANGUAGE_IDS: frozenset[str] = frozenset(
    lang
    for lang, spec in LANGUAGE_REGISTRY.items()
    if supports_semantic_chunking(spec)
)

# Languages indexed as text without a Tree-sitter grammar in LANGUAGE_REGISTRY.
TEXT_ONLY_LANGUAGES: dict[str, list[str]] = {
    'dart': ['.dart'],
    'swift': ['.swift'],
    'sql': ['.sql', '.psql'],
    'markdown': ['.md', '.markdown', '.rst'],
}


def resolve_intelligence_tier(
    *,
    language: str | None,
    indexing_mode: str | None,
    chunk_strategy: str | None,
) -> IntelligenceTier:
    """Derive the intelligence tier for a file or retrieval hit."""
    mode = (indexing_mode or '').strip().lower()
    strategy = (chunk_strategy or '').strip().lower()
    lang = (language or '').strip().lower()

    if mode == 'ast' and not strategy and lang in TIER_FULL_LANGUAGE_IDS:
        return IntelligenceTier.FULL
    if mode == 'ast' and strategy == 'ast_semantic':
        if lang in TIER_FULL_LANGUAGE_IDS or not lang:
            return IntelligenceTier.FULL
    if mode == 'ast' and strategy and strategy != 'ast_semantic':
        return IntelligenceTier.PARSE
    if mode in {'ast_empty', 'parse_error', 'source_text', 'text', 'unsupported_extension'}:
        return IntelligenceTier.TEXT
    if lang in TIER_FULL_LANGUAGE_IDS and strategy == 'ast_semantic':
        return IntelligenceTier.FULL
    if strategy in {'text_structural', 'text_sliding'}:
        return IntelligenceTier.TEXT
    if lang in TIER_FULL_LANGUAGE_IDS:
        return IntelligenceTier.PARSE
    return IntelligenceTier.UNKNOWN


def supports_call_graph(tier: IntelligenceTier | str) -> bool:
    """Return whether call-chain and dependency APIs are meaningful for this tier."""
    value = tier if isinstance(tier, IntelligenceTier) else IntelligenceTier(str(tier))
    return value == IntelligenceTier.FULL


def should_persist_call_edges(file_result: dict) -> bool:
    """Return True only when parsed calls align with AST function chunks."""
    if not file_result.get('calls'):
        return False
    if file_result.get('indexing_mode') != 'ast':
        return False
    chunks = file_result.get('chunks') or []
    if not chunks:
        return False
    def _is_ast_semantic(chunk: dict) -> bool:
        strategy = chunk.get('chunk_strategy')
        if strategy is None:
            return False
        return str(strategy) in {'ast_semantic', 'ChunkStrategy.AST_SEMANTIC'}

    return all(_is_ast_semantic(c) for c in chunks)


def summarize_ingest_tiers(parsed_files: list[dict]) -> dict[str, int]:
    """Count files by intelligence tier for index_folder summaries."""
    counts: dict[str, int] = {t.value: 0 for t in IntelligenceTier}
    for item in parsed_files:
        chunks = item.get('chunks') or []
        strategy = chunks[0].get('chunk_strategy') if chunks else None
        tier = resolve_intelligence_tier(
            language=item.get('language'),
            indexing_mode=item.get('indexing_mode'),
            chunk_strategy=str(strategy) if strategy else None,
        )
        counts[tier.value] = counts.get(tier.value, 0) + 1
    return counts


def _extensions_for_language(lang_id: str) -> list[str]:
    from infrastructure.parser.path_language import EXTENSION_TO_LANGUAGE

    return sorted(
        ext for ext, mapped in EXTENSION_TO_LANGUAGE.items() if mapped == lang_id
    )


def _parsing_mode(tier: IntelligenceTier) -> str:
    if tier == IntelligenceTier.FULL:
        return 'tree_sitter_ast_semantic'
    if tier == IntelligenceTier.PARSE:
        return 'tree_sitter_parse_text_fallback'
    if tier == IntelligenceTier.TEXT:
        return 'text_heuristic'
    return 'unknown'


def get_language_manifest() -> dict[str, dict]:
    """Return a JSON-serializable manifest for editor and agent UIs."""
    out: dict[str, dict] = {}
    for lang_id, spec in LANGUAGE_REGISTRY.items():
        tier = IntelligenceTier.FULL if supports_semantic_chunking(spec) else IntelligenceTier.PARSE
        out[lang_id] = {
            'tier': tier.value,
            'parsing_mode': _parsing_mode(tier),
            'chunk_strategy': 'ast_semantic' if tier == IntelligenceTier.FULL else 'text_structural',
            'call_graph': supports_semantic_chunking(spec),
            'extensions': _extensions_for_language(lang_id),
            'parser': 'tree_sitter',
        }
    for lang_id, extensions in TEXT_ONLY_LANGUAGES.items():
        if lang_id not in out:
            out[lang_id] = {
                'tier': IntelligenceTier.TEXT.value,
                'parsing_mode': _parsing_mode(IntelligenceTier.TEXT),
                'chunk_strategy': 'text_structural',
                'call_graph': False,
                'extensions': extensions,
                'parser': 'text_heuristic',
            }
    return out


def get_language_support_summary() -> dict:
    """Grouped language support for APIs and setup diagnostics."""
    manifest = get_language_manifest()
    by_tier: dict[str, list[str]] = {t.value: [] for t in IntelligenceTier}
    for lang_id, entry in sorted(manifest.items()):
        by_tier.setdefault(entry['tier'], []).append(lang_id)
    return {
        'tiers': by_tier,
        'full_count': len(by_tier.get(IntelligenceTier.FULL.value, [])),
        'parse_count': len(by_tier.get(IntelligenceTier.PARSE.value, [])),
        'text_count': len(by_tier.get(IntelligenceTier.TEXT.value, [])),
        'languages': manifest,
        'documentation': 'backend/infra/codeweave/docs/LANGUAGE_SUPPORT.md',
    }
