"""Probe Tree-sitter grammars and map repository file extensions to languages.

Used by setup and diagnostics to warm only grammars present in a codebase and
to verify ``tree-sitter-languages`` loads on the current platform.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from application.ingestion.source_filter import iter_ingestible_files, iter_repo_files
from infrastructure.parser.language_specs import LANGUAGE_REGISTRY, supports_semantic_chunking
from infrastructure.parser.path_language import EXTENSION_TO_LANGUAGE, infer_language


@dataclass(frozen=True)
class GrammarProbeResult:
    language: str
    ok: bool
    error: str | None = None


def scan_repository_extensions(
    root: Path,
    *,
    max_files: int = 50_000,
) -> Counter[str]:
    """Count lowercase file suffixes under ``root``, skipping dependency trees."""
    counts: Counter[str] = Counter()
    for path in iter_repo_files(root, max_files=max_files):
        suffix = path.suffix.lower()
        if suffix:
            counts[suffix] += 1
    return counts


def extensions_to_languages(extensions: Iterable[str]) -> set[str]:
    """Map file suffixes (e.g. ``.py``) to Tree-sitter language ids."""
    langs: set[str] = set()
    for ext in extensions:
        key = ext if ext.startswith('.') else f'.{ext}'
        lang = EXTENSION_TO_LANGUAGE.get(key.lower())
        if lang:
            langs.add(lang)
    return langs


def languages_for_ingestible_files(root: Path) -> set[str]:
    """Return Tree-sitter language ids required to index code files under ``root``."""
    langs: set[str] = set()
    for path, kind in iter_ingestible_files(root):
        if kind != 'code':
            continue
        try:
            langs.add(infer_language(path))
        except Exception:
            continue
    return langs


def probe_language(language: str) -> GrammarProbeResult:
    """Load parser and compile function query for ``language``."""
    from infrastructure.parser.tree_sitter_parser import build_query_map, get_parser

    lang = language.lower().strip()
    if lang not in LANGUAGE_REGISTRY:
        return GrammarProbeResult(lang, ok=False, error=f'unknown language id {lang!r}')
    try:
        get_parser(lang)
        build_query_map(lang)
    except Exception as exc:
        return GrammarProbeResult(lang, ok=False, error=str(exc))
    return GrammarProbeResult(lang, ok=True)


def probe_languages(languages: Iterable[str]) -> list[GrammarProbeResult]:
    """Probe each language id; results are sorted by language name."""
    return sorted(
        (probe_language(lang) for lang in sorted({l.lower().strip() for l in languages})),
        key=lambda item: item.language,
    )


def probe_repository(root: Path) -> dict:
    """Scan ``root`` and return extension counts plus grammar probe results."""
    extensions = scan_repository_extensions(root)
    code_langs = languages_for_ingestible_files(root)
    ext_langs = extensions_to_languages(extensions)
    target_langs = code_langs | ext_langs
    results = probe_languages(target_langs)
    failed = [r for r in results if not r.ok]
    return {
        'root': str(root.resolve()),
        'extension_counts': dict(extensions.most_common(30)),
        'languages_detected': sorted(target_langs),
        'grammars_probed': len(results),
        'grammars_ok': len(results) - len(failed),
        'grammars_failed': [{'language': r.language, 'error': r.error} for r in failed],
        'semantic_languages': sorted(
            lang for lang in target_langs
            if lang in LANGUAGE_REGISTRY and supports_semantic_chunking(LANGUAGE_REGISTRY[lang])
        ),
    }
