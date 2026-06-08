"""CodeWeave Studio entry point for repository intelligence.

All product code should call :class:`RepositoryIntelligenceService` only — not
FAISS, Postgres, or ingestion internals directly.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from application.graph.build_graph import build_architecture_graph
from application.graph.call_chain import build_call_chain
from application.graph.node_detail import get_node_detail
from application.ingestion.index_folder import index_folder
from application.ingestion.language_capabilities import (
    get_language_manifest,
    get_language_support_summary,
    resolve_intelligence_tier,
    supports_call_graph,
)
from application.ingestion.path_utils import relative_to_repo, resolve_repo_path
from application.ingestion.repository_reset import reset_repository_index
from application.ingestion.update_files import (
    sync_changed_repository_files,
    update_repository_file,
)
from application.retrieval.context_package import build_context_package
from application.retrieval.retrieve_chunks import retrieve_chunks
from infrastructure.db.bootstrap import ensure_db_ready
from infrastructure.db.models.chunk_model import ChunkModel
from infrastructure.db.models.file_model import FileModel
from infrastructure.db.models.repository_model import RepositoryModel
from infrastructure.db.session import SessionLocal
from infrastructure.file.reader import read_file
from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class RepositoryIntelligenceService:
    """Embeddable repository intelligence SDK for CodeWeave Studio agents."""

    def __init__(self) -> None:
        self._ready = False

    def _ensure_ready(self) -> None:
        if not self._ready:
            ensure_db_ready()
            self._ready = True

    def _session(self):
        self._ensure_ready()
        return SessionLocal()

    @staticmethod
    def _parse_repository_id(repository_id: str) -> UUID:
        try:
            return UUID(str(repository_id))
        except ValueError as exc:
            raise ValueError(f'Invalid repository_id: {repository_id}') from exc

    def ingest_repository(
        self,
        repository_path: str,
        *,
        repository_name: str | None = None,
        embed: bool = True,
    ) -> dict:
        """Index a repository directory (parse, persist, optionally embed and graph)."""
        folder = Path(repository_path).expanduser().resolve()
        if not folder.is_dir():
            raise ValueError(f'Repository path is not a directory: {repository_path}')
        name = repository_name or folder.name
        summary = index_folder(folder, repository_name=name, embed=embed)
        repository_id = summary.get('repository_id')
        if not repository_id:
            return summary
        session = self._session()
        try:
            build_architecture_graph(session, UUID(str(repository_id)))
            session.commit()
        finally:
            session.close()
        logger.info('ingest_repository: completed for %s -> %s', folder, repository_id)
        return summary

    def parse_repository(
        self,
        repository_path: str,
        *,
        repository_name: str | None = None,
    ) -> dict:
        """Parse and persist graph rows without embedding or FAISS (fast path)."""
        return self.ingest_repository(
            repository_path,
            repository_name=repository_name,
            embed=False,
        )

    def delete_repository(self, repository_id: str) -> dict:
        """Remove all indexed data and the repository row."""
        repo_uuid = self._parse_repository_id(repository_id)
        session = self._session()
        try:
            repo = session.get(RepositoryModel, repo_uuid)
            if repo is None:
                raise ValueError(f'Repository not found: {repository_id}')
            name = repo.name
            reset_repository_index(session, repo_uuid)
            session.delete(repo)
            session.commit()
            logger.info('delete_repository: removed %s', repository_id)
            return {'repository_id': str(repo_uuid), 'repository': name, 'deleted': True}
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def semantic_search(
        self,
        repository_id: str,
        query: str,
        top_k: int = 10,
    ) -> list[dict]:
        """Semantic search over indexed chunks for a repository."""
        repo_uuid = self._parse_repository_id(repository_id)
        session = self._session()
        try:
            return retrieve_chunks(session, repo_uuid, query, top_k=top_k)
        finally:
            session.close()

    def get_node_details(self, node_id: str) -> dict | None:
        """Return rich detail for a graph node id (``type:uuid``)."""
        session = self._session()
        try:
            return get_node_detail(session, node_id)
        finally:
            session.close()

    def get_call_chain(
        self,
        repository_id: str,
        symbol_name: str,
        *,
        file_path: str | None = None,
        max_depth: int = 8,
    ) -> dict:
        """Return upstream/downstream call chains for ``symbol_name``.

        Pass ``file_path`` (repository-relative) to scope homonyms in polyglot repos.
        """
        repo_uuid = self._parse_repository_id(repository_id)
        session = self._session()
        try:
            return build_call_chain(
                session,
                repo_uuid,
                symbol_name,
                file_path=file_path,
                max_depth=max_depth,
            )
        finally:
            session.close()

    def get_architecture_graph(self, repository_id: str) -> dict:
        """Return hierarchy nodes and call/contains edges."""
        repo_uuid = self._parse_repository_id(repository_id)
        session = self._session()
        try:
            data = build_architecture_graph(session, repo_uuid)
            if not data.get('root_id'):
                raise ValueError(f'Repository not found: {repository_id}')
            return data
        finally:
            session.close()

    def get_file_contents(self, repository_id: str, file_path: str) -> dict:
        """Read UTF-8 source and indexing metadata for a repository-relative path."""
        repo_uuid = self._parse_repository_id(repository_id)
        session = self._session()
        try:
            repo = session.get(RepositoryModel, repo_uuid)
            if repo is None:
                raise ValueError(f'Repository not found: {repository_id}')
            normalized = file_path.replace('\\', '/').lstrip('/')
            basename = normalized.rsplit('/', 1)[-1]
            candidates = (
                session.query(FileModel)
                .filter(FileModel.repository_id == repo_uuid)
                .filter(
                    FileModel.file_path.endswith(normalized)
                    | FileModel.file_path.endswith('/' + normalized)
                    | FileModel.file_path.endswith(basename)
                )
                .all()
            )
            match = None
            for row in candidates:
                display = (
                    relative_to_repo(row.file_path, repo.root_path, repo.name)
                    if repo.root_path
                    else row.file_path.replace('\\', '/')
                )
                if display == normalized:
                    match = row
                    break
            if match is None and len(candidates) == 1:
                match = candidates[0]
            if match is None:
                for row in candidates:
                    display = (
                        relative_to_repo(row.file_path, repo.root_path, repo.name)
                        if repo.root_path
                        else row.file_path.replace('\\', '/')
                    )
                    if display.endswith('/' + normalized) or display.endswith(normalized):
                        match = row
                        break
            if match is None:
                raise ValueError(f'File not found in repository: {file_path}')

            sample_chunk = (
                session.query(ChunkModel)
                .filter_by(file_id=match.id)
                .order_by(ChunkModel.start_line.asc().nullsfirst())
                .first()
            )
            chunk_strategy = sample_chunk.chunk_strategy if sample_chunk else None

            abs_path = resolve_repo_path(match.file_path, repo.root_path) if repo.root_path else Path(match.file_path)
            raw = read_file(str(abs_path))
            content = raw.decode('utf-8', errors='replace')
            display_path = (
                relative_to_repo(match.file_path, repo.root_path, repo.name)
                if repo.root_path
                else match.file_path
            )
            tier = resolve_intelligence_tier(
                language=match.language,
                indexing_mode=match.indexing_mode,
                chunk_strategy=chunk_strategy,
            )
            return {
                'repository_id': str(repo_uuid),
                'file_path': display_path,
                'language': match.language,
                'indexing_mode': match.indexing_mode,
                'indexing_notice': match.indexing_notice,
                'chunk_strategy': chunk_strategy,
                'intelligence_tier': tier.value,
                'call_graph_available': supports_call_graph(tier),
                'content': content,
                'line_count': len(content.splitlines()),
            }
        finally:
            session.close()

    def get_language_capabilities(self) -> dict:
        """Return the language capability manifest (tiers, extensions, call graph)."""
        return get_language_manifest()

    def get_language_support_summary(self) -> dict:
        """Return grouped tiers plus per-language parsing modes for agents and setup."""
        return get_language_support_summary()

    def build_context_package(self, repository_id: str, goal: str) -> dict:
        """Primary agent interface: goal-oriented repository context bundle."""
        repo_uuid = self._parse_repository_id(repository_id)
        session = self._session()
        try:
            return build_context_package(session, repository_id=repo_uuid, goal=goal)
        finally:
            session.close()

    def update_file(
        self,
        repository_id: str,
        file_path: str,
        *,
        embed: bool = True,
        force: bool = False,
    ) -> dict:
        """Re-index a single file when its on-disk content changed.

        Compares SHA-256 content hash against the stored index and skips
        unchanged files unless ``force`` is True. Rebuilds FAISS from all
        repository chunks when ``embed`` is True so vectors stay aligned.
        """
        repo_uuid = self._parse_repository_id(repository_id)
        session = self._session()
        try:
            result = update_repository_file(
                session,
                repo_uuid,
                file_path,
                embed=embed,
                force=force,
            )
            session.commit()
            logger.info(
                'update_file: repository=%s path=%s status=%s',
                repository_id,
                file_path,
                result.get('status'),
            )
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def sync_changed_files(
        self,
        repository_id: str,
        *,
        embed: bool = True,
        force: bool = False,
    ) -> dict:
        """Re-index all indexed files whose on-disk hash differs from the index."""
        repo_uuid = self._parse_repository_id(repository_id)
        session = self._session()
        try:
            result = sync_changed_repository_files(
                session,
                repo_uuid,
                embed=embed,
                force=force,
            )
            session.commit()
            logger.info(
                'sync_changed_files: repository=%s updated=%s',
                repository_id,
                result.get('files_updated'),
            )
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
