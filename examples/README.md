# Examples

## Basic Vault Setup

1. Copy `.orag.toml.example` to your vault root as `.orag.toml`
2. Edit the file to configure your vault name and directories
3. Run `orag index` from your vault directory

## Example Vault Structure

```
my-vault/
├── .orag.toml          # Vault configuration
├── Content/
│   ├── Notes/
│   │   ├── note1.md
│   │   └── note2.md
│   └── Projects/
│       └── project1.md
├── .vector_store/      # Auto-created by orag
│   └── chroma.sqlite3
└── Index.md
```

## Example Usage

```bash
# Index the vault
cd /path/to/my-vault
orag index

# Search
orag search "machine learning concepts"

# Get RAG context
orag rag "explain neural networks" --show-context

# View stats
orag stats
```

## Integration with Claude

Create a `SKILL.md` in your vault:

```markdown
# Vault RAG Skill

This vault is indexed with orag for semantic search.

## Usage

When answering questions about vault content, always use:

\`\`\`bash
# Get comprehensive context
orag rag "user question" --json

# Search for specific documents
orag search "keywords" --json
\`\`\`

Parse the JSON output and use the retrieved context to inform your responses.
Always cite sources from the `sources` field in the response.
```
