# Obsidian RAG CLI

🔍 Semantic search and RAG (Retrieval Augmented Generation) for Obsidian vaults using LlamaIndex + ChromaDB.

## Features

- **Semantic Search**: Find relevant documents using vector similarity
- **RAG Context Retrieval**: Get aggregated context for LLM augmentation
- **Local Vector Database**: Fast, persistent ChromaDB storage
- **Simple Configuration**: TOML-based vault configuration
- **Beautiful CLI**: Rich console output with tables, panels, and colors
- **Fast**: 10-50ms query times after indexing

## Installation

```bash
# Install from GitHub
pip install git+https://github.com/avatarye/obsidian-rag-cli.git

# Or install locally with uv (for development)
cd obsidian-rag-cli
uv pip install -e .
```

## Quick Start

### 1. Initialize Vault Configuration

```bash
cd /path/to/your/vault
orag init
```

This creates a `.orag.toml` file with sensible defaults. You can also:

```bash
# Custom configuration
orag init --name my-vault --dirs "Content,Notes,docs"

# Interactive mode
orag init -i

# Or edit .orag.toml manually
```

### 2. Index Your Vault

```bash
orag index
```

### 3. Search and Query

```bash
# Semantic search
orag search "python virtual environments"

# Get RAG context for LLM
orag rag "how to setup development environment" --show-context

# View statistics
orag stats
```

## Commands

### `orag init`

Initialize vault configuration with `.orag.toml`.

```bash
# Auto-detect vault name, use current directory
orag init

# Custom vault name
orag init --name my-vault

# Custom directories to index
orag init --dirs "Content,Notes,docs"

# Interactive mode with prompts
orag init -i

# Force overwrite existing config
orag init --force
```

### `orag index`

Index all markdown files in configured directories.

```bash
# Index vault (looks for .orag.toml in current dir)
orag index

# Index specific vault
orag index --vault /path/to/vault

# Force rebuild
orag index --force

# Verbose output
orag index --verbose

# JSON output
orag index --json
```

### `orag search`

Search for relevant documents.

```bash
# Basic search
orag search "query text"

# Control results
orag search "query" --top-k 10 --min-score 0.5

# JSON output (for programmatic use)
orag search "query" --json
```

### `orag rag`

Get aggregated context for RAG.

```bash
# Get RAG context
orag rag "what is the main topic"

# Control context size
orag rag "query" --max-chars 8000 --sources 3

# Show full context
orag rag "query" --show-context

# JSON output
orag rag "query" --json
```

### `orag stats`

Show vault and index statistics.

```bash
orag stats
orag stats --json
```

### `orag reindex`

Clear and rebuild index.

```bash
orag reindex
orag reindex --yes  # Skip confirmation
```

## Configuration

### Global Configuration

Located at `~/.config/orag/config.toml` (auto-created on first run):

```toml
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
```

### Vault Configuration

Located at `{vault_root}/.orag.toml` (you create this):

```toml
[vault]
name = "brazil"

# List of directories to index (relative to vault root)
dirs = [
    "Content",
    "Notes",
    "."
]

[storage]
# Vector store location (relative to vault root)
vector_store = ".vector_store"
```

## Integration with Claude Code

Create a `SKILL.md` in your vault to enable Claude to use the RAG system:

```markdown
# RAG Skill

When users ask questions about this vault, use:

\`\`\`bash
# For comprehensive context
orag rag "user's question" --json

# For document discovery
orag search "keywords" --json
\`\`\`

Parse JSON output and use retrieved context to inform responses.
```

## Architecture

```
CLI (Click + Rich)
  ↓
API (ObsidianRAG)
  ↓
Logic Layer
  ├─ VaultIndexer: Scan dirs, chunk documents
  ├─ VectorSearcher: Query vector DB
  └─ ConfigLoader: Load TOML configs
```

## Output Examples

### Search Results

```
🔍 Search: "brazil build targets" (12.3ms)

┌──────┬────────────────────────────────┬───────┬─────────────────┐
│ Rank │ Document                       │ Score │ Preview         │
├──────┼────────────────────────────────┼───────┼─────────────────┤
│  1   │ concepts-build-targets.md      │ 0.850 │ Build targets...│
│  2   │ ref-brazil-build.md            │ 0.820 │ brazil-build... │
└──────┴────────────────────────────────┴───────┴─────────────────┘
```

### RAG Context

```
╭─ RAG Context ──────────────────────────────────────╮
│ Query: what is bb release                          │
│ Context: 8,542 chars from 3 sources                │
│ Retrieved in: 18.7ms                               │
╰────────────────────────────────────────────────────╯

Sources:
  1. concepts-build-targets.md (score: 0.850)
  2. ref-brazil-build.md (score: 0.820)
  3. concepts-package-builder.md (score: 0.760)
```

## Technical Details

- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384 dims)
- **Vector Database**: ChromaDB with persistent storage
- **Chunking**: 512 chars with 50 char overlap
- **File Types**: Markdown (.md) only
- **Performance**: 10-50ms query time (after initialization)

## Development

```bash
# Clone repo
git clone https://github.com/avatarye/obsidian-rag-cli.git
cd obsidian-rag-cli

# Install with uv
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black obsidian_rag/
ruff check obsidian_rag/
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.

## Acknowledgments

- [LlamaIndex](https://www.llamaindex.ai/) - RAG framework
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Beautiful console output
