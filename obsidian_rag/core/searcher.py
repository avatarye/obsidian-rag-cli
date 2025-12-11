"""Vector search and RAG functionality."""

import time
from pathlib import Path
from typing import List
from loguru import logger

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb

from .models import (
    VaultConfig,
    GlobalConfig,
    SearchResult,
    SearchResponse,
    RAGSource,
    RAGResponse,
    VaultStats,
)


class VectorSearcher:
    """Search vector database and retrieve RAG context."""

    def __init__(self, vault_path: Path, vault_config: VaultConfig, global_config: GlobalConfig):
        self.vault_path = vault_path
        self.vault_config = vault_config
        self.global_config = global_config
        self.vector_store_path = vault_path / vault_config.vector_store
        self._index = None
        self._embed_model = None

    def _load_index(self) -> VectorStoreIndex:
        """Load existing vector index."""
        if self._index is not None:
            return self._index

        if not self.vector_store_path.exists():
            raise FileNotFoundError(
                f"Vector store not found at {self.vector_store_path}. "
                f"Please run 'orag index' first."
            )

        # Initialize embedding model
        self._embed_model = HuggingFaceEmbedding(model_name=self.global_config.embedding_model)

        # Load ChromaDB
        db = chromadb.PersistentClient(path=str(self.vector_store_path))

        try:
            collection = db.get_collection(name=self.vault_config.name)
        except Exception:
            raise ValueError(
                f"Collection '{self.vault_config.name}' not found. "
                f"Please run 'orag index' first."
            )

        # Load vector store
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Load index
        self._index = VectorStoreIndex.from_vector_store(
            vector_store, storage_context=storage_context, embed_model=self._embed_model
        )

        logger.info("Vector index loaded successfully")
        return self._index

    def search(self, query: str, top_k: int = 5, min_score: float = 0.3) -> SearchResponse:
        """Perform semantic search."""
        start_time = time.time()

        try:
            index = self._load_index()
            retriever = index.as_retriever(similarity_top_k=top_k)

            # Retrieve nodes
            nodes = retriever.retrieve(query)

            # Convert to search results
            results = []
            for node in nodes:
                score = node.score if node.score is not None else 0.0

                # Filter by minimum score
                if score < min_score:
                    continue

                result = SearchResult(
                    file_path=node.metadata.get("file_path", "unknown"),
                    score=score,
                    chunk=node.text,
                    metadata=node.metadata,
                )
                results.append(result)

            elapsed_ms = (time.time() - start_time) * 1000

            return SearchResponse(
                status="success",
                query=query,
                results=results,
                count=len(results),
                query_time_ms=elapsed_ms,
            )

        except Exception as e:
            logger.error(f"Search error: {e}")
            return SearchResponse(
                status="error",
                query=query,
                results=[],
                count=0,
                query_time_ms=(time.time() - start_time) * 1000,
            )

    def get_rag_context(
        self, query: str, max_chars: int = 10000, max_sources: int = 5
    ) -> RAGResponse:
        """Retrieve aggregated context for RAG."""
        start_time = time.time()

        try:
            # First perform search
            search_response = self.search(
                query, top_k=max_sources, min_score=self.global_config.min_relevance_score
            )

            if search_response.status == "error" or not search_response.results:
                return RAGResponse(
                    status="error",
                    query=query,
                    context="",
                    sources=[],
                    context_length=0,
                    query_time_ms=(time.time() - start_time) * 1000,
                )

            # Aggregate context from results
            context_parts = []
            sources = []
            total_chars = 0

            for result in search_response.results:
                chunk = result.chunk
                chunk_len = len(chunk)

                # Check if adding this chunk exceeds limit
                if total_chars + chunk_len > max_chars:
                    remaining = max_chars - total_chars
                    if remaining > 100:  # Only add if meaningful content remains
                        chunk = chunk[:remaining] + "..."
                        context_parts.append(f"## {result.file_path}\n\n{chunk}")
                    break

                context_parts.append(f"## {result.file_path}\n\n{chunk}")
                total_chars += chunk_len

                sources.append(
                    RAGSource(
                        file_name=result.metadata.get("file_name", "unknown"),
                        file_path=result.file_path,
                        relevance_score=result.score,
                        char_count=chunk_len,
                    )
                )

            context = "\n\n---\n\n".join(context_parts)
            elapsed_ms = (time.time() - start_time) * 1000

            return RAGResponse(
                status="success",
                query=query,
                context=context,
                sources=sources,
                context_length=len(context),
                query_time_ms=elapsed_ms,
            )

        except Exception as e:
            logger.error(f"RAG error: {e}")
            return RAGResponse(
                status="error",
                query=query,
                context="",
                sources=[],
                context_length=0,
                query_time_ms=(time.time() - start_time) * 1000,
            )

    def get_stats(self) -> VaultStats:
        """Get vault and index statistics."""
        try:
            if not self.vector_store_path.exists():
                return VaultStats(
                    status="error",
                    vault_name=self.vault_config.name,
                    vault_path=str(self.vault_path),
                    document_count=0,
                    chunk_count=0,
                    vector_store_size_mb=0,
                    embedding_model=self.global_config.embedding_model,
                )

            # Load ChromaDB
            db = chromadb.PersistentClient(path=str(self.vector_store_path))
            collection = db.get_collection(name=self.vault_config.name)

            # Get collection stats
            chunk_count = collection.count()

            # Calculate directory size
            total_size = sum(
                f.stat().st_size for f in self.vector_store_path.rglob("*") if f.is_file()
            )
            size_mb = total_size / (1024 * 1024)

            # Estimate document count from metadata (approximate)
            # In a real implementation, you might want to store this separately
            document_count = len(
                set(
                    meta.get("file_path", "")
                    for meta in collection.get(include=["metadatas"]).get("metadatas", [])
                )
            )

            return VaultStats(
                status="success",
                vault_name=self.vault_config.name,
                vault_path=str(self.vault_path),
                document_count=document_count if document_count > 0 else chunk_count // 3,
                chunk_count=chunk_count,
                vector_store_size_mb=round(size_mb, 2),
                embedding_model=self.global_config.embedding_model,
            )

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return VaultStats(
                status="error",
                vault_name=self.vault_config.name,
                vault_path=str(self.vault_path),
                document_count=0,
                chunk_count=0,
                vector_store_size_mb=0,
                embedding_model=self.global_config.embedding_model,
            )
