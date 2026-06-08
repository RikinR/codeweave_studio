from __future__ import annotations

"""File discovery and classification for repository ingestion.

Pipeline stage: **scan** (before parse).

Walks repository trees, skips dependency and cache directories, and classifies
paths as code, context (Dockerfile, README, YAML), or plain text. Used by
:mod:`index_folder` to choose :mod:`process_code` vs :mod:`text_chunking`.

Policy: index every plausible text/source file. Skip only dependency trees,
secrets, lockfiles, and binary blobs.
"""
from pathlib import Path
from typing import Literal

from infrastructure.parser.path_language import is_supported_extension

FileKind = Literal['code', 'context', 'text']
"""Ingestion category assigned by :func:`classify_ingestible_file`."""

# Dependency, build output, and tooling caches — not project source.
SKIP_DIR_NAMES = frozenset({
    '.git', '.hg', '.svn', '.venv', 'venv', 'virtualenv', 'env',
    'node_modules', '__pycache__', '.mypy_cache', '.pytest_cache', '.tox', '.nox',
    'dist', 'build', 'target', '.idea', '.vscode', '.cursor', 'htmlcov', '.eggs',
    'site-packages', '.npm', '.yarn', '.pnpm-store', 'coverage', '.gradle', '.next',
    '.nuxt', 'out', '.dart_tool', '.pub-cache', 'vendor', 'pods', 'carthage',
    'deriveddata', '.terraform', '.serverless', 'bower_components', 'jspm_packages',
    'cache', '.cache', 'tmp', 'temp', 'bin', 'obj',
})

_CONTEXT_EXTENSIONS = frozenset({
    '.dockerfile', '.markdown', '.md', '.rst', '.toml', '.yaml', '.yml',
})
_CONTEXT_FILE_NAMES = frozenset({
    'containerfile', 'dockerfile', 'pipfile',
    'requirements-dev.txt', 'requirements-prod.txt', 'requirements.txt',
})

# Plain text and data files (no Tree-sitter AST path).
_TEXT_EXTENSIONS = frozenset({
    '.cfg', '.conf', '.ini', '.mdown', '.properties', '.text', '.txt',
    '.log', '.logs', '.out', '.trace',
    '.json', '.jsonc', '.json5',
    '.sql', '.psql',
    '.tf', '.tfvars', '.hcl',
    '.dot', '.gv', '.ejs', '.hbs', '.ql', '.regex',
})

# Markup/styles indexed as text (no reliable AST chunking in this stack).
_TEXT_INDEXED_UNSUPPORTED_EXTENSIONS = frozenset({
    '.css', '.htm', '.html', '.sass', '.scss',
})

# Languages without a bundled Tree-sitter grammar — still indexed via text chunkers.
_SOURCE_TEXT_EXTENSIONS = frozenset({
    '.dart', '.swift', '.vue', '.svelte', '.gradle', '.groovy', '.proto',
    '.xml', '.xsl', '.xslt', '.nim', '.zig', '.v', '.sv', '.tcl', '.erb',
    '.haml', '.slim', '.mustache', '.twig', '.fs', '.fsx', '.vb', '.pas',
    '.pp', '.asm', '.s', '.cmake', '.nix', '.lean', '.agda', '.pest',
    '.graphql', '.gql', '.sol', '.solidity', '.wat', '.wast', '.wgsl',
    '.cu', '.cuh', '.ino', '.pde',
})

_EXTENSIONLESS_TEXT_NAMES = frozenset({
    'makefile', 'gnumakefile', 'jenkinsfile', 'rakefile', 'gemfile', 'podfile',
    'brewfile', 'procfile', 'vagrantfile', 'berksfile', 'guardfile', 'capfile',
    'justfile', 'taskfile',
})

_SKIP_FILE_NAMES = frozenset({
    '.dockerignore', '.editorconfig', '.gitattributes', '.gitignore',
    '.prettierignore', '.prettierrc',
    'cargo.lock', 'gemfile.lock', 'package-lock.json', 'poetry.lock', 'yarn.lock',
})
_SKIP_NAME_PREFIXES = ('.env',)

# Do not index multi‑MB single files (logs, dumps, generated blobs).
_MAX_INDEX_BYTES = 10 * 1024 * 1024
_TEXT_PROBE_BYTES = 8192


def is_text_indexed_unsupported_extension(path: Path) -> bool:
    """Return True for extensions indexed as text without Tree-sitter support (e.g. HTML)."""
    return path.suffix.lower() in _TEXT_INDEXED_UNSUPPORTED_EXTENSIONS


def is_source_text_extension(path: Path) -> bool:
    """Return True for source languages indexed via text chunkers (no bundled grammar)."""
    return path.suffix.lower() in _SOURCE_TEXT_EXTENSIONS


def _path_has_skipped_dir(path: Path) -> bool:
    return any(part.lower() in SKIP_DIR_NAMES for part in path.parts)


def _is_skipped_file_name(name: str) -> bool:
    lower = name.lower()
    if lower in _SKIP_FILE_NAMES:
        return True
    if lower.startswith(_SKIP_NAME_PREFIXES) and not lower.endswith(('.example', '.sample', '.template')):
        return True
    return False


def _is_context_file(path: Path) -> bool:
    lower = path.name.lower()
    if lower in _CONTEXT_FILE_NAMES:
        return True
    if path.suffix.lower() in _CONTEXT_EXTENSIONS:
        return True
    if lower.startswith('docker-compose') and lower.endswith(('.yml', '.yaml')):
        return True
    if lower.startswith('compose.') and lower.endswith(('.yml', '.yaml')):
        return True
    return False


def _is_text_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix in _TEXT_EXTENSIONS:
        return True
    if suffix in _TEXT_INDEXED_UNSUPPORTED_EXTENSIONS:
        return True
    if suffix in _SOURCE_TEXT_EXTENSIONS:
        return True
    if path.name.lower() in _EXTENSIONLESS_TEXT_NAMES:
        return True
    return False


def _file_too_large(path: Path) -> bool:
    try:
        return path.stat().st_size > _MAX_INDEX_BYTES
    except OSError:
        return True


def _looks_like_text_file(path: Path) -> bool:
    """Heuristic: UTF-8 decodable sample without NUL bytes."""
    try:
        with path.open('rb') as handle:
            sample = handle.read(_TEXT_PROBE_BYTES)
    except OSError:
        return False
    if not sample:
        return False
    if b'\x00' in sample:
        return False
    sample.decode('utf-8')
    return True


def classify_ingestible_file(path: Path) -> FileKind | None:
    """Classify a file as code, context, text, or skip (``None``)."""
    if not path.is_file():
        return None
    if _path_has_skipped_dir(path):
        return None
    if _is_skipped_file_name(path.name):
        return None
    if _file_too_large(path):
        return None
    if _is_context_file(path):
        return 'context'
    if path.suffix.lower() in _TEXT_INDEXED_UNSUPPORTED_EXTENSIONS:
        return 'text'
    if _is_text_file(path):
        return 'text'
    if is_supported_extension(path):
        return 'code'
    if _looks_like_text_file(path):
        return 'text'
    return None


def iter_repo_files(folder: Path, *, max_files: int = 50_000):
    """Yield regular files under ``folder``, skipping dependency and cache directories."""
    if not folder.is_dir():
        return
    seen = 0
    stack: list[Path] = [folder]
    while stack and seen < max_files:
        current = stack.pop()
        try:
            children = sorted(current.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            continue
        for child in children:
            if seen >= max_files:
                return
            if child.is_dir():
                if child.name.lower() in SKIP_DIR_NAMES:
                    continue
                stack.append(child)
            elif child.is_file():
                seen += 1
                yield child


def iter_ingestible_files(folder: Path):
    """Yield ``(path, kind)`` for ingestible files under ``folder``."""
    for path in iter_repo_files(folder):
        kind = classify_ingestible_file(path)
        if kind is not None:
            yield path, kind
