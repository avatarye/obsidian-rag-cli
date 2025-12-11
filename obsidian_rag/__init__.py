"""
Obsidian RAG CLI - Semantic search and RAG for Obsidian vaults.

A command-line tool for semantic search and retrieval-augmented generation (RAG)
on Obsidian markdown vaults using LlamaIndex and ChromaDB.

Key Features:
    - Semantic search across markdown documents
    - RAG context retrieval for LLM augmentation
    - Local vector database (ChromaDB)
    - TOML-based configuration
    - Beautiful CLI with Rich console output

Example Usage:
    # Initialize vault configuration
    $ orag init

    # Index vault documents
    $ orag index

    # Search for documents
    $ orag search "query text" --top-k 5

    # Get RAG context
    $ orag rag "question" --json

API Usage:
    >>> from obsidian_rag import ObsidianRAG
    >>> client = ObsidianRAG("/path/to/vault")
    >>> result = client.search("query text")
    >>> rag_context = client.get_rag_context("question")

For more information, see: https://github.com/avatarye/obsidian-rag-cli
"""

__version__ = "0.1.0"

from .api import ObsidianRAG

__all__ = ["ObsidianRAG"]
