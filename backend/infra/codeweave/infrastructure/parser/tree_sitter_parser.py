"""Tree-sitter parser and query helpers for multi-language AST extraction.

Bridges :mod:`infrastructure.parser.language_specs` query definitions to native
grammars from ``tree-sitter-languages``. Used by ingestion
(:mod:`application.ingestion.process_code`) and graph-related parsing.
"""

from __future__ import annotations

from typing import Protocol, cast

from tree_sitter import Parser
from tree_sitter_languages import get_language

from infrastructure.logging.logger import get_logger
from infrastructure.parser.language_specs import get_language_spec

logger = get_logger(__name__)

_language_cache: dict[str, object] = {}
_parser_cache: dict[str, Parser] = {}


class _ParserSetLanguage(Protocol):
    def set_language(self, language: object) -> None:
        ...


def _cached_language(lang: str) -> object:
    key = lang.lower().strip()
    if key not in _language_cache:
        get_language_spec(key)
        try:
            _language_cache[key] = get_language(key)
        except Exception as exc:
            logger.error(
                'cached_language: native grammar load failed for language=%s',
                key,
                exc_info=True,
            )
            raise RuntimeError(
                f'Failed to load Tree-sitter grammar for {key!r}. '
                'Ensure tree-sitter-languages includes this grammar on your platform.'
            ) from exc
    return _language_cache[key]


def get_parser(lang: str) -> Parser:
    """Return a cached Tree-sitter parser configured for ``lang``."""
    key = lang.lower().strip()
    cached = _parser_cache.get(key)
    if cached is not None:
        return cached
    logger.debug('get_parser: language=%s', key)
    language = _cached_language(key)
    parser = Parser()
    cast(_ParserSetLanguage, parser).set_language(language)
    _parser_cache[key] = parser
    logger.info('get_parser: ready for language=%s', key)
    return parser


def get_query(lang: str, queries: str):
    """Compile a Tree-sitter query string for ``lang``."""
    logger.debug('get_query: compile query for language=%s', lang)
    language = _cached_language(lang)
    try:
        return language.query(queries)
    except Exception as exc:
        logger.error('get_query: invalid query for language=%s: %s', lang, exc, exc_info=True)
        raise


def build_query_map(lang: str) -> dict[str, object]:
    """Return compiled queries for all keys in the language spec (functions, classes, etc.)."""
    spec = get_language_spec(lang)
    return {key: get_query(lang, qsrc.strip()) for key, qsrc in spec.queries.items()}
