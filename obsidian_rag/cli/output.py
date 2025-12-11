"""Rich console output utilities."""

import json
from typing import Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree

from ..core import SearchResponse, RAGResponse, IndexResult, VaultStats

console = Console()


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"✓ {message}", style="bold green")


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"✗ {message}", style="bold red")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"ℹ {message}", style="bold blue")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"⚠ {message}", style="bold yellow")


def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    json_str = json.dumps(data, indent=2)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    console.print(syntax)


def print_index_result(result: IndexResult, as_json: bool = False) -> None:
    """Print indexing result."""
    if as_json:
        print_json(result.model_dump())
        return

    if result.status == "error":
        print_error("Indexing failed")
        for error in result.errors:
            console.print(f"  • {error}", style="red")
        return

    # Create success tree
    tree = Tree(f"✓ Indexed [bold green]{result.documents_indexed}[/] documents in [cyan]{result.time_elapsed_ms / 1000:.1f}s[/]")
    tree.add(f"[dim]Chunks created:[/] {result.chunks_created}")
    tree.add(f"[dim]Vector store:[/] {result.vector_store_path}")

    if result.chunks_created > 0:
        avg_chunk = result.documents_indexed * 1000 // result.chunks_created if result.chunks_created else 0
        tree.add(f"[dim]Average doc/chunk ratio:[/] ~1:{result.chunks_created // result.documents_indexed if result.documents_indexed else 0}")

    console.print(tree)


def print_search_results(response: SearchResponse, as_json: bool = False) -> None:
    """Print search results."""
    if as_json:
        print_json(response.model_dump())
        return

    if response.status == "error":
        print_error("Search failed")
        return

    if not response.results:
        print_warning(f"No results found for: '{response.query}'")
        return

    # Header
    console.print(f"\n🔍 Search: [bold cyan]'{response.query}'[/] ({response.query_time_ms:.1f}ms)\n")

    # Results table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="dim", width=6)
    table.add_column("Document", style="cyan")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Preview", style="dim")

    for i, result in enumerate(response.results, 1):
        preview = result.chunk[:80].replace("\n", " ") + "..." if len(result.chunk) > 80 else result.chunk.replace("\n", " ")
        table.add_row(
            str(i),
            result.file_path,
            f"{result.score:.3f}",
            preview,
        )

    console.print(table)
    console.print(f"\n💡 [dim]Tip: Use --json for machine-readable output[/]\n")


def print_rag_context(response: RAGResponse, as_json: bool = False, show_context: bool = False) -> None:
    """Print RAG context."""
    if as_json:
        print_json(response.model_dump())
        return

    if response.status == "error":
        print_error("RAG retrieval failed")
        return

    if not response.sources:
        print_warning(f"No context found for: '{response.query}'")
        return

    # Header panel
    panel_content = f"""[bold]Query:[/] {response.query}
[bold]Context:[/] {response.context_length:,} chars from {len(response.sources)} sources
[bold]Retrieved in:[/] {response.query_time_ms:.1f}ms"""

    console.print(Panel(panel_content, title="RAG Context", border_style="blue"))

    # Sources
    console.print("\n[bold]Sources:[/]")
    for i, source in enumerate(response.sources, 1):
        console.print(f"  {i}. [cyan]{source.file_name}[/] (score: {source.relevance_score:.3f}, {source.char_count} chars)")

    # Context preview or full
    if show_context:
        console.print("\n[bold]Context:[/]\n")
        syntax = Syntax(response.context, "markdown", theme="monokai", line_numbers=False)
        console.print(syntax)
    else:
        console.print("\n💡 [dim]Use --show-context to display full context[/]\n")


def print_stats(stats: VaultStats, as_json: bool = False) -> None:
    """Print vault statistics."""
    if as_json:
        print_json(stats.model_dump())
        return

    if stats.status == "error":
        print_error("Unable to retrieve stats")
        return

    # Create stats panel
    content = f"""[bold]Vault:[/] {stats.vault_name}
[bold]Path:[/] {stats.vault_path}
[bold]Documents:[/] {stats.document_count}
[bold]Chunks:[/] {stats.chunk_count}
[bold]Vector Store Size:[/] {stats.vector_store_size_mb} MB
[bold]Embedding Model:[/] {stats.embedding_model}"""

    console.print(Panel(content, title="Vault Statistics", border_style="green"))
