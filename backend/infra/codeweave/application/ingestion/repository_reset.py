"""Clear persisted index data before a full re-ingest of a repository."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from infrastructure.db.models.file_model import FileModel
from infrastructure.logging.logger import get_logger
from infrastructure.vector.config import faiss_index_path_for_repository
from infrastructure.vector.faiss_cache import invalidate as invalidate_faiss_cache

logger = get_logger(__name__)


def reset_repository_index(session: Session, repository_id: UUID) -> None:
    """Remove graph rows and the FAISS index for ``repository_id`` before re-indexing.

    Deletes all :class:`FileModel` rows (cascades functions, chunks, classes, and
    call edges) and removes the on-disk FAISS index so embedding indices restart
    at 0 without ``uq_chunks_repository_embedding_index`` violations.
    """
    deleted = (
        session.query(FileModel)
        .filter_by(repository_id=repository_id)
        .delete(synchronize_session=False)
    )
    session.flush()
    index_path = faiss_index_path_for_repository(repository_id)
    if index_path.is_file():
        index_path.unlink()
        logger.info('reset_repository_index: removed FAISS index %s', index_path)
    invalidate_faiss_cache(repository_id)
    logger.info(
        'reset_repository_index: cleared repository_id=%s (%d files removed)',
        repository_id,
        deleted,
    )


def delete_faiss_index_file(repository_id: UUID) -> None:
    """Remove only the FAISS index file (e.g. parse-only ingest)."""
    index_path = faiss_index_path_for_repository(repository_id)
    if index_path.is_file():
        Path(index_path).unlink()
    invalidate_faiss_cache(repository_id)
