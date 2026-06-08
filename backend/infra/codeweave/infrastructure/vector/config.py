"""On-disk FAISS index paths and layout.

Each repository gets ``data/faiss/{repository_id}.index``, opened by
:class:`infrastructure.vector.faiss_store.FaissStore` and cached in
:mod:`infrastructure.vector.faiss_cache`.
"""

from pathlib import Path
from uuid import UUID
from infrastructure.embeddings.config import EMBEDDING_DIMENSION
from infrastructure.env_loader import FAISS_DIR, load_studio_env
from infrastructure.logging.logger import get_logger

load_studio_env()
logger = get_logger(__name__)
FAISS_INDEX_DIR = FAISS_DIR
FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)

def faiss_index_path_for_repository(repository_id: UUID) -> Path:
    """Return the filesystem path for a repository's FAISS index file."""
    return FAISS_INDEX_DIR / f'{repository_id}.index'
logger.debug('vector store: index_dir=%s dimension=%d', FAISS_INDEX_DIR, EMBEDDING_DIMENSION)
