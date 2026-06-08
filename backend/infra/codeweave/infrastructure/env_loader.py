"""Load CodeWeave Studio environment from ``backend/.env`` (idempotent).

All runtime state for this subsystem stays under ``backend/infra/codeweave/``
(models, FAISS indexes, logs) and PostgreSQL database ``coweavestudio`` only.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/infra/codeweave/infrastructure/env_loader.py -> parents[3] == backend/
_BACKEND_DIR = Path(__file__).resolve().parents[3]
CODEWEAVE_DIR = _BACKEND_DIR / 'infra' / 'codeweave'
ENV_FILE = _BACKEND_DIR / '.env'
DATA_DIR = CODEWEAVE_DIR / 'data'
FAISS_DIR = DATA_DIR / 'faiss'
LOG_DIR = CODEWEAVE_DIR / 'logs'

# Hard-coded Studio intelligence database — not configurable to avoid accidental
# sharing with other projects' databases on the same Postgres instance.
STUDIO_DB_NAME = 'coweavestudio'

_BLOCKED_DB_NAMES = frozenset(
    {
        'code_weave',
        'codeweave',
        'postgres',
        'template0',
        'template1',
    }
)

_loaded = False


def load_studio_env(*, require_file: bool = True) -> Path:
    """Load ``backend/.env`` once; return the env file path used.

    Studio ``.env`` values override existing process env for codeweave keys so a
    shared shell cannot point this project at another database.
    """
    global _loaded
    if not _loaded:
        if require_file and not ENV_FILE.is_file():
            raise FileNotFoundError(
                f'CodeWeave Studio requires {ENV_FILE}. '
                f'Copy backend/.env.example and set DB_PASSWORD.'
            )
        if ENV_FILE.is_file():
            load_dotenv(ENV_FILE, override=True)
        _loaded = True
        _pin_local_cache_dirs()
    return ENV_FILE


def _pin_local_cache_dirs() -> None:
    """Keep Hugging Face / sentence-transformers caches inside this repo."""
    cache = models_dir()
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('HF_HOME', str(cache))
    os.environ.setdefault('SENTENCE_TRANSFORMERS_HOME', str(cache))
    os.environ.setdefault('TRANSFORMERS_CACHE', str(cache))


def models_dir() -> Path:
    """Directory for cached sentence-transformer weights."""
    raw = os.getenv('CODEWEAVE_MODELS_DIR')
    path = Path(raw).expanduser() if raw else CODEWEAVE_DIR / 'models'
    if not path.is_absolute():
        path = (_BACKEND_DIR / path).resolve()
    return path


def require_studio_database_name() -> str:
    """Return ``DB_NAME`` after verifying it is the dedicated Studio database."""
    load_studio_env()
    name = (os.getenv('DB_NAME') or '').strip()
    if not name:
        raise RuntimeError(
            f'DB_NAME is not set. Use DB_NAME={STUDIO_DB_NAME} in {ENV_FILE}.'
        )
    if name != STUDIO_DB_NAME:
        raise RuntimeError(
            f'DB_NAME must be exactly {STUDIO_DB_NAME!r} for CodeWeave Studio isolation '
            f'(got {name!r}). Other databases on this machine must not be used.'
        )
    if name in _BLOCKED_DB_NAMES:
        raise RuntimeError(f'DB_NAME {name!r} is blocked for Studio intelligence.')
    return name
