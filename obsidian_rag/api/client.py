"""API client for obsidian-rag-cli."""

from pathlib import Path
from typing import Optional, Callable
from loguru import logger

from ..core import (
    ConfigLoader,
    VaultIndexer,
    VectorSearcher,
    SearchResponse,
    RAGResponse,
    IndexResult,
    VaultStats,
)


class ObsidianRAG:
    """High-level API for Obsidian RAG operations."""

    def __init__(self, vault_path: Optional[str] = None):
        """
        Initialize ObsidianRAG client.

        Args:
            vault_path: Path to vault root. If None, searches for .orag.toml in current/parent dirs.
        """
        if vault_path:
            self.vault_path = Path(vault_path).resolve()
        else:
            self.vault_path = ConfigLoader.find_vault_root()

        # Load configurations
        self.global_config = ConfigLoader.load_global_config()
        self.vault_config = ConfigLoader.load_vault_config(self.vault_path)

        # Configure logging
        logger.remove()  # Remove default handler
        logger.add(
            lambda msg: None,  # Suppress by default, CLI will add handlers
            level=self.global_config.log_level,
        )

    def index_vault(
        self, force: bool = False, progress_callback: Optional[Callable] = None
    ) -> IndexResult:
        """
        Index all documents in vault.

        Args:
            force: If True, clear existing index before indexing
            progress_callback: Optional callback for progress updates

        Returns:
            IndexResult with indexing statistics
        """
        indexer = VaultIndexer(self.vault_path, self.vault_config, self.global_config)

        if force:
            indexer.clear_index()

        return indexer.index_vault(progress_callback)

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> SearchResponse:
        """
        Perform semantic search on indexed documents.

        Args:
            query: Search query
            top_k: Number of results to return (uses global config default if None)
            min_score: Minimum relevance score (uses global config default if None)

        Returns:
            SearchResponse with results
        """
        searcher = VectorSearcher(self.vault_path, self.vault_config, self.global_config)

        return searcher.search(
            query,
            top_k=top_k or self.global_config.default_top_k,
            min_score=min_score or self.global_config.min_relevance_score,
        )

    def get_rag_context(
        self,
        query: str,
        max_chars: Optional[int] = None,
        max_sources: Optional[int] = None,
    ) -> RAGResponse:
        """
        Get aggregated context for RAG augmentation.

        Args:
            query: Query to find relevant context for
            max_chars: Maximum characters in context (uses global config default if None)
            max_sources: Maximum number of source documents (default: 5)

        Returns:
            RAGResponse with aggregated context and sources
        """
        searcher = VectorSearcher(self.vault_path, self.vault_config, self.global_config)

        return searcher.get_rag_context(
            query,
            max_chars=max_chars or self.global_config.default_max_chars,
            max_sources=max_sources or 5,
        )

    def get_stats(self) -> VaultStats:
        """
        Get vault and index statistics.

        Returns:
            VaultStats with vault information
        """
        searcher = VectorSearcher(self.vault_path, self.vault_config, self.global_config)
        return searcher.get_stats()

    def reindex_vault(self, progress_callback: Optional[Callable] = None) -> IndexResult:
        """
        Clear and rebuild vector index.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            IndexResult with indexing statistics
        """
        return self.index_vault(force=True, progress_callback=progress_callback)
