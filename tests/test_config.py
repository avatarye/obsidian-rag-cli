"""Tests for configuration management."""

import pytest
from pathlib import Path
import tempfile
import toml

from obsidian_rag.core import ConfigLoader, VaultConfig, GlobalConfig


def test_global_config_creation():
    """Test that global config is created with defaults."""
    config = GlobalConfig()
    assert config.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert config.chunk_size == 512
    assert config.chunk_overlap == 50


def test_vault_config_loading():
    """Test loading vault configuration from TOML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = Path(tmpdir)
        config_file = vault_path / ".orag.toml"

        # Create test config
        config_data = {
            "vault": {"name": "test-vault", "dirs": ["Content", "."]},
            "storage": {"vector_store": ".vector_store"},
        }
        with open(config_file, "w") as f:
            toml.dump(config_data, f)

        # Load config
        vault_config = ConfigLoader.load_vault_config(vault_path)

        assert vault_config.name == "test-vault"
        assert vault_config.dirs == ["Content", "."]
        assert vault_config.vector_store == ".vector_store"


def test_vault_config_missing():
    """Test error when vault config is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = Path(tmpdir)

        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_vault_config(vault_path)


def test_vault_config_defaults():
    """Test vault config defaults."""
    config = VaultConfig(name="test")
    assert config.name == "test"
    assert config.dirs == ["."]
    assert config.vector_store == ".vector_store"
