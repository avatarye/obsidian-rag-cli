"""Data models for obsidian-rag-cli."""

from typing import List, Optional
from pydantic import BaseModel, Field


class VaultConfig(BaseModel):
    """Vault configuration from .orag.toml."""

    name: str
    dirs: List[str] = Field(default_factory=lambda: ["."])
    vector_store: str = ".vector_store"


class GlobalConfig(BaseModel):
    """Global configuration from ~/.config/orag/config.toml."""

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 50
    default_top_k: int = 5
    default_max_chars: int = 10000
    min_relevance_score: float = 0.3
    log_level: str = "INFO"


class SearchResult(BaseModel):
    """Single search result."""

    file_path: str
    score: float
    chunk: str
    line_range: Optional[tuple[int, int]] = None
    metadata: dict = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Search API response."""

    status: str
    query: str
    results: List[SearchResult]
    count: int
    query_time_ms: float


class RAGSource(BaseModel):
    """Source document for RAG context."""

    file_name: str
    file_path: str
    relevance_score: float
    char_count: int


class RAGResponse(BaseModel):
    """RAG API response."""

    status: str
    query: str
    context: str
    sources: List[RAGSource]
    context_length: int
    query_time_ms: float


class IndexResult(BaseModel):
    """Index operation result."""

    status: str
    documents_indexed: int
    chunks_created: int
    time_elapsed_ms: float
    vector_store_path: str
    errors: List[str] = Field(default_factory=list)


class VaultStats(BaseModel):
    """Vault statistics."""

    status: str
    vault_name: str
    vault_path: str
    document_count: int
    chunk_count: int
    vector_store_size_mb: float
    embedding_model: str
    last_indexed: Optional[str] = None
