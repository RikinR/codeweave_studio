#!/usr/bin/env bash
# Coweave Studio — one-shot local setup.
# - Ensures backend/.env exists
# - Creates backend/.venv and installs Python deps from backend/requirements.txt
# - Downloads embedding model into backend/infra/codeweave/models/
# - Creates Postgres database coweavestudio (if missing) and ORM tables

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
CODEWEAVE="$BACKEND/infra/codeweave"
MODELS_DIR="$CODEWEAVE/models"
REQUIREMENTS="$BACKEND/requirements.txt"
# Single project venv (override with COWEAVE_VENV only).
VENV="${COWEAVE_VENV:-$BACKEND/.venv}"

# Strip optional quotes and whitespace from a .env value.
env_value() {
  local key="$1"
  local line raw
  line="$(grep -E "^${key}=" "$BACKEND/.env" | tail -1 || true)"
  raw="${line#*=}"
  raw="${raw#"${raw%%[![:space:]]*}"}"
  raw="${raw%"${raw##*[![:space:]]}"}"
  raw="${raw#\"}"
  raw="${raw%\"}"
  raw="${raw#\'}"
  raw="${raw%\'}"
  printf '%s' "$raw"
}

echo "==> Coweave Studio setup"
echo "    root:      $ROOT"
echo "    codeweave: $CODEWEAVE"
echo "    venv:      $VENV"
echo "    models:    $MODELS_DIR"

if [[ ! -f "$BACKEND/.env" ]]; then
  if [[ -f "$BACKEND/.env.example" ]]; then
    cp "$BACKEND/.env.example" "$BACKEND/.env"
    echo "==> Created $BACKEND/.env from .env.example — edit DB_PASSWORD and GROQ_API_KEY"
  else
    echo "ERROR: Missing $BACKEND/.env and .env.example" >&2
    exit 1
  fi
fi

DB_NAME_VAL="$(env_value DB_NAME)"
if [[ "$DB_NAME_VAL" != "coweavestudio" ]]; then
  echo "ERROR: DB_NAME must be exactly coweavestudio (found: ${DB_NAME_VAL:-<unset>})." >&2
  echo "       This project must not share a database with other apps." >&2
  exit 1
fi
if [[ "$(env_value DB_USER)" == "postgres" ]]; then
  echo "WARN:  DB_USER=postgres is a shared superuser. For isolation, use scripts/isolation.sql" >&2
  echo "       and DB_USER=coweavestudio_app in backend/.env" >&2
fi

if [[ ! -d "$VENV" ]]; then
  echo "==> Creating venv at $VENV"
  python3 -m venv "$VENV"
fi

# shellcheck source=/dev/null
source "$VENV/bin/activate"

echo "==> Installing dependencies"
pip install -q --upgrade pip
if [[ ! -f "$REQUIREMENTS" ]]; then
  echo "ERROR: Missing $REQUIREMENTS" >&2
  exit 1
fi
pip install -q -r "$REQUIREMENTS"

mkdir -p "$MODELS_DIR" "$CODEWEAVE/data/faiss"

echo "==> Probing Tree-sitter grammars for extensions in this project"
SCAN_ROOT="${COWEAVE_SCAN_ROOT:-$ROOT}"
python <<PY
import json
import sys
from pathlib import Path

sys.path.insert(0, "$CODEWEAVE")
from infrastructure.parser.grammar_probe import probe_repository

report = probe_repository(Path("$SCAN_ROOT"))
failed = report.get("grammars_failed") or []
print(
    f"   extensions scanned: {len(report.get('extension_counts') or {})} types, "
    f"languages: {len(report.get('languages_detected') or [])}, "
    f"grammars OK: {report.get('grammars_ok', 0)}/{report.get('grammars_probed', 0)}"
)
if report.get("semantic_languages"):
    print(f"   full-tier (AST) in repo: {', '.join(report['semantic_languages'])}")
for item in failed:
    print(f"   WARN grammar {item['language']}: {item['error']}", file=sys.stderr)
if failed:
    sys.exit(1)
PY

export PYTHONPATH="$CODEWEAVE"
export CODEWEAVE_MODELS_DIR="$MODELS_DIR"
export HF_HOME="$MODELS_DIR"
export SENTENCE_TRANSFORMERS_HOME="$MODELS_DIR"
export TRANSFORMERS_CACHE="$MODELS_DIR"

echo "==> Downloading embedding model (first run may take a few minutes)"
python <<'PY'
from infrastructure.env_loader import ENV_FILE, load_studio_env, models_dir
from infrastructure.embeddings.config import LOCAL_EMBEDDING_MODEL, EMBEDDING_DIMENSION
from infrastructure.embeddings.local_embedder import embed_texts

load_studio_env()
cache = models_dir()
cache.mkdir(parents=True, exist_ok=True)
print(f"env file:     {ENV_FILE}")
print(f"model:        {LOCAL_EMBEDDING_MODEL}")
print(f"dimension:    {EMBEDDING_DIMENSION}")
print(f"cache folder: {cache}")
embed_texts(["coweave studio warmup"])
print("embedding model: OK")
PY

echo "==> Ensuring Postgres database and schema (DB_NAME from backend/.env)"
python <<'PY'
from infrastructure.env_loader import load_studio_env
from infrastructure.db.config import DB_NAME
from infrastructure.db.bootstrap import ensure_db_ready

load_studio_env()
print(f"database: {DB_NAME}")
ensure_db_ready()
print("database bootstrap: OK")
PY

echo ""
echo "Coweave Studio is ready."
echo "  Activate:  source $VENV/bin/activate"
echo "  PYTHONPATH=$CODEWEAVE"
echo "  Use: from intelligence_service import RepositoryIntelligenceService"
