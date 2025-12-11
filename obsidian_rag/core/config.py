"""Configuration management for obsidian-rag-cli."""

import os
from pathlib import Path
from typing import Optional
import toml
from loguru import logger

from .models import VaultConfig, GlobalConfig


class ConfigLoader:
    """Load and manage vault and global configurations."""

    GLOBAL_CONFIG_DIR = Path.home() / ".config" / "orag"
    GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.toml"
    VAULT_CONFIG_FILE = ".orag.toml"

    @classmethod
    def load_global_config(cls) -> GlobalConfig:
        """Load global configuration, create default if not exists."""
        if not cls.GLOBAL_CONFIG_FILE.exists():
            logger.info("Global config not found, creating default...")
            cls.create_default_global_config()

        try:
            data = toml.load(cls.GLOBAL_CONFIG_FILE)
            return GlobalConfig(
                embedding_model=data.get("embedding", {}).get(
                    "model", "sentence-transformers/all-MiniLM-L6-v2"
                ),
                chunk_size=data.get("chunking", {}).get("size", 512),
                chunk_overlap=data.get("chunking", {}).get("overlap", 50),
                default_top_k=data.get("search", {}).get("default_top_k", 5),
                default_max_chars=data.get("search", {}).get("default_max_chars", 10000),
                min_relevance_score=data.get("search", {}).get("min_relevance_score", 0.3),
                log_level=data.get("logging", {}).get("level", "INFO"),
            )
        except Exception as e:
            logger.warning(f"Error loading global config: {e}, using defaults")
            return GlobalConfig()

    @classmethod
    def create_default_global_config(cls) -> None:
        """Create default global configuration file."""
        cls.GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        default_config = """# Global RAG system settings

[embedding]
model = "sentence-transformers/all-MiniLM-L6-v2"

[chunking]
size = 512
overlap = 50

[search]
default_top_k = 5
default_max_chars = 10000
min_relevance_score = 0.3

[logging]
level = "INFO"
"""
        cls.GLOBAL_CONFIG_FILE.write_text(default_config)
        logger.info(f"Created default global config at {cls.GLOBAL_CONFIG_FILE}")

    @classmethod
    def load_vault_config(cls, vault_path: Path) -> VaultConfig:
        """Load vault configuration from .orag.toml."""
        config_file = vault_path / cls.VAULT_CONFIG_FILE

        if not config_file.exists():
            raise FileNotFoundError(
                f"No .orag.toml found in {vault_path}. "
                f"Please create one with vault name and dirs to index."
            )

        try:
            data = toml.load(config_file)
            vault_data = data.get("vault", {})
            storage_data = data.get("storage", {})

            return VaultConfig(
                name=vault_data.get("name", vault_path.name),
                dirs=vault_data.get("dirs", ["."]),
                vector_store=storage_data.get("vector_store", ".vector_store"),
            )
        except Exception as e:
            raise ValueError(f"Error parsing .orag.toml: {e}")

    @classmethod
    def find_vault_root(cls, start_path: Optional[Path] = None) -> Path:
        """Find vault root by looking for .orag.toml in current or parent directories."""
        if start_path is None:
            start_path = Path.cwd()

        current = start_path.resolve()

        # Check current directory and parents up to 5 levels
        for _ in range(5):
            if (current / cls.VAULT_CONFIG_FILE).exists():
                return current
            if current == current.parent:
                break
            current = current.parent

        raise FileNotFoundError(
            f"No .orag.toml found in {start_path} or parent directories. "
            f"Please create one in your vault root."
        )
