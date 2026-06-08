"""Incremental re-indexing of individual repository files.

Updates graph rows and FAISS vectors for changed files without a full
``index_folder`` wipe. Used by :mod:`intelligence_service`.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from application.ingestion.chunk_text import chunk_to_embedding_text
from application.ingestion.path_utils import relative_to_repo, resolve_repo_path
from application.ingestion.persist import (
    IndexBatch,
    file_content_hash,
    replace_repository_chunks,
)
from application.ingestion.source_filter import classify_ingestible_file
from infrastructure.db.models.chunk_model import ChunkModel
from infrastructure.db.models.file_model import FileModel
from infrastructure.db.models.repository_model import RepositoryModel
from infrastructure.embeddings.local_embedder import EmbeddingError, embed_texts
from infrastructure.logging.logger import get_logger
from infrastructure.vector.config import faiss_index_path_for_repository
from infrastructure.vector.faiss_cache import invalidate as invalidate_faiss_cache
from infrastructure.vector.faiss_store import FaissStore

logger = get_logger(__name__)


def _normalize_repo_path(file_path: str) -> str:
    return file_path.replace('\\', '/').lstrip('/')


def _display_file_path(file_row: FileModel, repo: RepositoryModel) -> str:
    if repo.root_path:
        return relative_to_repo(file_row.file_path, repo.root_path, repo.name)
    return file_row.file_path.replace('\\', '/')


def _chunk_item_from_row(chunk: ChunkModel, *, file_path: str) -> dict:
    fn = chunk.function
    chunk_dict = {
        'name': fn.name,
        'code': chunk.content,
        'description': fn.description,
        'chunk_type': chunk.chunk_type or 'function',
        'start_line': chunk.start_line,
        'end_line': chunk.end_line,
        'start': fn.start_byte,
        'end': fn.end_byte,
    }
    return {
        'repository_id': chunk.repository_id,
        'file_id': chunk.file_id,
        'function_id': fn.id,
        'chunk': chunk_dict,
        'text': chunk_to_embedding_text(file_path, chunk_dict),
        'file_path': file_path,
    }


def snapshot_repository_chunk_items(session: Session, repository_id: UUID) -> list[dict]:
    """Capture embedding payloads for all chunks currently stored in Postgres."""
    chunks = (
        session.query(ChunkModel)
        .filter_by(repository_id=repository_id)
        .options(
            joinedload(ChunkModel.function),
            joinedload(ChunkModel.file).joinedload(FileModel.repository),
        )
        .all()
    )
    items: list[dict] = []
    for chunk in chunks:
        repo = chunk.file.repository
        file_path = _display_file_path(chunk.file, repo)
        items.append(_chunk_item_from_row(chunk, file_path=file_path))
    items.sort(key=lambda item: (item['file_path'], item['chunk'].get('start_line') or 0))
    return items


def _parse_disk_file(abs_path: Path) -> dict | None:
    from application.ingestion.process_code import process_code_file
    from application.ingestion.text_chunking import process_text_file

    kind = classify_ingestible_file(abs_path)
    if kind is None:
        return None
    path = str(abs_path)
    if kind in ('context', 'text'):
        return process_text_file(path)
    return process_code_file(path)


def _remove_indexed_file(session: Session, repository_id: UUID, rel_path: str) -> bool:
    existing = (
        session.query(FileModel)
        .filter_by(repository_id=repository_id, file_path=rel_path)
        .one_or_none()
    )
    if existing is None:
        return False
    session.delete(existing)
    session.flush()
    return True


def rebuild_faiss_for_repository(
    session: Session,
    repository: RepositoryModel,
    chunk_items: list[dict],
) -> int:
    """Re-embed ``chunk_items`` and rewrite the repository FAISS index."""
    index_path = faiss_index_path_for_repository(repository.id)
    invalidate_faiss_cache(repository.id)
    if index_path.is_file():
        index_path.unlink()

    if not chunk_items:
        logger.info('rebuild_faiss_for_repository: no chunks for %s', repository.id)
        return 0

    texts = [item['text'] for item in chunk_items]
    vectors = embed_texts(texts)
    store = FaissStore(index_path=index_path)
    store.load_or_create()
    embedding_indices = store.add(vectors)
    store.save()
    invalidate_faiss_cache(repository.id)
    replace_repository_chunks(
        session,
        repository.id,
        chunk_items,
        embedding_indices,
    )
    logger.info(
        'rebuild_faiss_for_repository: repository=%s chunks=%d',
        repository.id,
        len(chunk_items),
    )
    return len(chunk_items)


def update_repository_file(
    session: Session,
    repository_id: UUID,
    file_path: str,
    *,
    embed: bool = True,
    force: bool = False,
) -> dict:
    """Re-index one repository-relative file when its on-disk content changed."""
    repo = session.get(RepositoryModel, repository_id)
    if repo is None:
        raise ValueError(f'Repository not found: {repository_id}')
    if not repo.root_path:
        raise ValueError(f'Repository has no root_path; run full ingest first: {repository_id}')

    if Path(file_path).is_absolute():
        rel_path = _normalize_repo_path(
            relative_to_repo(file_path, repo.root_path, repo.name)
        )
    else:
        rel_path = _normalize_repo_path(file_path)
    abs_path = resolve_repo_path(rel_path, repo.root_path)

    if not abs_path.is_file():
        removed = _remove_indexed_file(session, repository_id, rel_path)
        chunk_items = snapshot_repository_chunk_items(session, repository_id)
        chunks_stored = 0
        if embed and chunk_items:
            chunks_stored = rebuild_faiss_for_repository(session, repo, chunk_items)
        elif embed and not chunk_items:
            index_path = faiss_index_path_for_repository(repository_id)
            if index_path.is_file():
                index_path.unlink()
            invalidate_faiss_cache(repository_id)
            session.query(ChunkModel).filter_by(repository_id=repository_id).delete(
                synchronize_session=False
            )
        return {
            'repository_id': str(repository_id),
            'file_path': rel_path,
            'status': 'removed' if removed else 'not_found',
            'updated': removed,
            'skipped': False,
            'chunks': chunks_stored,
            'embeddings': chunks_stored,
        }

    current_hash = file_content_hash(abs_path)
    existing = (
        session.query(FileModel)
        .filter_by(repository_id=repository_id, file_path=rel_path)
        .one_or_none()
    )
    if existing is not None and existing.file_hash == current_hash and not force:
        return {
            'repository_id': str(repository_id),
            'file_path': rel_path,
            'status': 'unchanged',
            'updated': False,
            'skipped': True,
            'file_hash': current_hash,
        }

    kind = classify_ingestible_file(abs_path)
    if kind is None:
        removed = _remove_indexed_file(session, repository_id, rel_path)
        remaining = [
            item
            for item in snapshot_repository_chunk_items(session, repository_id)
            if item['file_path'] != rel_path
        ]
        chunks_stored = 0
        if embed:
            chunks_stored = rebuild_faiss_for_repository(session, repo, remaining)
        return {
            'repository_id': str(repository_id),
            'file_path': rel_path,
            'status': 'removed_non_ingestible' if removed else 'skipped_non_ingestible',
            'updated': removed,
            'skipped': not removed,
        }

    try:
        parsed = _parse_disk_file(abs_path)
    except (OSError, UnicodeError, RuntimeError, ValueError, KeyError) as exc:
        logger.warning('update_repository_file: parse failed %s: %s', rel_path, exc)
        return {
            'repository_id': str(repository_id),
            'file_path': rel_path,
            'status': 'parse_error',
            'updated': False,
            'skipped': False,
            'error': str(exc),
        }

    if parsed is None:
        return {
            'repository_id': str(repository_id),
            'file_path': rel_path,
            'status': 'parse_error',
            'updated': False,
            'skipped': False,
            'error': 'parser returned no result',
        }

    parsed['file'] = str(abs_path)
    preserved_items = [
        item
        for item in snapshot_repository_chunk_items(session, repository_id)
        if item['file_path'] != rel_path
    ]

    batch = IndexBatch(repo)
    batch.add_file(session, parsed)
    batch.record_all_calls(session)

    chunks_stored = 0
    embeddings = 0
    if embed and (preserved_items or batch.pending):
        all_items = preserved_items + batch.pending
        all_items.sort(
            key=lambda item: (
                item['file_path'],
                item['chunk'].get('start_line') or 0,
            )
        )
        try:
            chunks_stored = rebuild_faiss_for_repository(session, repo, all_items)
            embeddings = chunks_stored
        except EmbeddingError:
            session.rollback()
            raise

    return {
        'repository_id': str(repository_id),
        'file_path': rel_path,
        'status': 'updated',
        'updated': True,
        'skipped': False,
        'file_hash': current_hash,
        'language': parsed.get('language'),
        'indexing_mode': parsed.get('indexing_mode'),
        'functions': batch.functions_indexed,
        'classes': batch.classes_indexed,
        'calls': batch.calls_indexed,
        'chunks': chunks_stored,
        'embeddings': embeddings,
    }


def sync_changed_repository_files(
    session: Session,
    repository_id: UUID,
    *,
    embed: bool = True,
    force: bool = False,
) -> dict:
    """Re-index indexed files whose on-disk hash differs from the stored hash."""
    repo = session.get(RepositoryModel, repository_id)
    if repo is None:
        raise ValueError(f'Repository not found: {repository_id}')
    if not repo.root_path:
        raise ValueError(f'Repository has no root_path; run full ingest first: {repository_id}')

    root = Path(repo.root_path)
    if not root.is_dir():
        raise ValueError(f'Repository root_path is not a directory: {repo.root_path}')

    indexed_files = (
        session.query(FileModel).filter_by(repository_id=repository_id).all()
    )
    results: list[dict] = []
    changed_paths: list[str] = []

    for file_row in indexed_files:
        rel_path = _display_file_path(file_row, repo)
        abs_path = resolve_repo_path(rel_path, repo.root_path)
        if not abs_path.is_file():
            changed_paths.append(rel_path)
            continue
        if force or file_row.file_hash != file_content_hash(abs_path):
            changed_paths.append(rel_path)

    if not changed_paths:
        return {
            'repository_id': str(repository_id),
            'status': 'unchanged',
            'files_checked': len(indexed_files),
            'files_updated': 0,
            'files_skipped': len(indexed_files),
            'results': [],
        }

    updated = 0
    skipped = 0
    for rel_path in sorted(changed_paths):
        result = update_repository_file(
            session,
            repository_id,
            rel_path,
            embed=embed,
            force=force,
        )
        results.append(result)
        if result.get('updated'):
            updated += 1
        elif result.get('skipped'):
            skipped += 1

    return {
        'repository_id': str(repository_id),
        'status': 'synced',
        'files_checked': len(indexed_files),
        'files_updated': updated,
        'files_skipped': skipped,
        'results': results,
    }
