"""Document indexer for obsidian-rag-cli."""

import time
from pathlib import Path
from typing import List, Callable, Optional
from loguru import logger

from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb

from .models import VaultConfig, GlobalConfig, IndexResult


class VaultIndexer:
    """Index markdown documents from vault directories."""

    def __init__(self, vault_path: Path, vault_config: VaultConfig, global_config: GlobalConfig):
        self.vault_path = vault_path
        self.vault_config = vault_config
        self.global_config = global_config
        self.vector_store_path = vault_path / vault_config.vector_store

    def scan_documents(self) -> List[Path]:
        """Scan vault directories for markdown files."""
        md_files = []

        for dir_path in self.vault_config.dirs:
            full_path = self.vault_path / dir_path

            if not full_path.exists():
                logger.warning(f"Directory not found: {full_path}")
                continue

            if full_path.is_file() and full_path.suffix == ".md":
                md_files.append(full_path)
            elif full_path.is_dir():
                md_files.extend(full_path.rglob("*.md"))

        # Remove duplicates and sort
        md_files = sorted(set(md_files))
        logger.info(f"Found {len(md_files)} markdown files")

        return md_files

    def load_documents(self, file_paths: List[Path]) -> List[Document]:
        """Load markdown files as LlamaIndex documents."""
        documents = []

        for file_path in file_paths:
            try:
                content = file_path.read_text(encoding="utf-8")
                relative_path = file_path.relative_to(self.vault_path)

                doc = Document(
                    text=content,
                    metadata={
                        "file_path": str(relative_path),
                        "file_name": file_path.name,
                        "vault": self.vault_config.name,
                    },
                )
                documents.append(doc)
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")

        logger.info(f"Loaded {len(documents)} documents")
        return documents

    def create_index(
        self, documents: List[Document], progress_callback: Optional[Callable] = None
    ) -> VectorStoreIndex:
        """Create vector index from documents."""
        # Initialize embedding model
        embed_model = HuggingFaceEmbedding(model_name=self.global_config.embedding_model)

        # Initialize ChromaDB
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        db = chromadb.PersistentClient(path=str(self.vector_store_path))

        # Create or get collection
        collection = db.get_or_create_collection(name=self.vault_config.name)

        # Create vector store
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Create text splitter
        text_splitter = SentenceSplitter(
            chunk_size=self.global_config.chunk_size,
            chunk_overlap=self.global_config.chunk_overlap,
        )

        # Create index
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embed_model=embed_model,
            transformations=[text_splitter],
            show_progress=True,
        )

        logger.info("Vector index created successfully")
        return index

    def index_vault(self, progress_callback: Optional[Callable] = None) -> IndexResult:
        """Index all documents in vault."""
        start_time = time.time()
        errors = []

        try:
            # Scan for documents
            file_paths = self.scan_documents()

            if not file_paths:
                return IndexResult(
                    status="error",
                    documents_indexed=0,
                    chunks_created=0,
                    time_elapsed_ms=0,
                    vector_store_path=str(self.vector_store_path),
                    errors=["No markdown files found in specified directories"],
                )

            # Load documents
            documents = self.load_documents(file_paths)

            # Create index
            index = self.create_index(documents, progress_callback)

            # Calculate stats
            elapsed_ms = (time.time() - start_time) * 1000

            # Estimate chunk count (approximate)
            total_chars = sum(len(doc.text) for doc in documents)
            chunks_created = total_chars // self.global_config.chunk_size

            return IndexResult(
                status="success",
                documents_indexed=len(documents),
                chunks_created=chunks_created,
                time_elapsed_ms=elapsed_ms,
                vector_store_path=str(self.vector_store_path),
                errors=errors,
            )

        except Exception as e:
            logger.error(f"Error indexing vault: {e}")
            return IndexResult(
                status="error",
                documents_indexed=0,
                chunks_created=0,
                time_elapsed_ms=(time.time() - start_time) * 1000,
                vector_store_path=str(self.vector_store_path),
                errors=[str(e)],
            )

    def clear_index(self) -> None:
        """Clear existing vector store."""
        if self.vector_store_path.exists():
            import shutil

            shutil.rmtree(self.vector_store_path)
            logger.info(f"Cleared vector store at {self.vector_store_path}")
