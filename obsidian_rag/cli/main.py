"""Main CLI entry point for orag."""

import sys
import click
from loguru import logger
from pathlib import Path

from .output import console, print_error
from ..api import ObsidianRAG


# Configure loguru
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
)


@click.group()
@click.version_option(version="0.1.0", prog_name="orag")
def cli():
    """
    🔍 Obsidian RAG CLI - Semantic search and RAG for Obsidian vaults.

    Create a .orag.toml file in your vault root to get started.
    """
    pass


@cli.command()
@click.option("--vault", type=click.Path(exists=True), help="Path to vault root")
@click.option("--force", is_flag=True, help="Clear and rebuild index")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed progress")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def index(vault, force, verbose, as_json):
    """Index vault documents to create vector database."""
    from .output import print_index_result, print_error

    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    try:
        client = ObsidianRAG(vault_path=vault)

        if not as_json:
            action = "Rebuilding" if force else "Building"
            console.print(f"{action} index for vault: [cyan]{client.vault_config.name}[/]")

        result = client.index_vault(force=force)
        print_index_result(result, as_json=as_json)

    except FileNotFoundError as e:
        print_error(str(e))
        console.print("\n💡 [dim]Create a .orag.toml file in your vault root with:[/]")
        console.print('[dim]  [vault]\\n  name = "my-vault"\\n  dirs = ["."][/]\n')
        sys.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        if verbose:
            logger.exception("Detailed error:")
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option("--vault", type=click.Path(exists=True), help="Path to vault root")
@click.option("--top-k", type=int, help="Number of results to return")
@click.option("--min-score", type=float, help="Minimum relevance score")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search(query, vault, top_k, min_score, as_json):
    """Search for relevant documents."""
    from .output import print_search_results, print_error

    try:
        client = ObsidianRAG(vault_path=vault)
        response = client.search(query, top_k=top_k, min_score=min_score)
        print_search_results(response, as_json=as_json)

    except FileNotFoundError as e:
        print_error(str(e))
        sys.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option("--vault", type=click.Path(exists=True), help="Path to vault root")
@click.option("--max-chars", type=int, help="Maximum characters in context")
@click.option("--sources", type=int, help="Maximum number of source documents")
@click.option("--show-context", is_flag=True, help="Display full context")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def rag(query, vault, max_chars, sources, show_context, as_json):
    """Get RAG context for a query."""
    from .output import print_rag_context, print_error

    try:
        client = ObsidianRAG(vault_path=vault)
        response = client.get_rag_context(query, max_chars=max_chars, max_sources=sources)
        print_rag_context(response, as_json=as_json, show_context=show_context)

    except FileNotFoundError as e:
        print_error(str(e))
        sys.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.option("--vault", type=click.Path(exists=True), help="Path to vault root")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def stats(vault, as_json):
    """Show vault and index statistics."""
    from .output import print_stats, print_error

    try:
        client = ObsidianRAG(vault_path=vault)
        vault_stats = client.get_stats()
        print_stats(vault_stats, as_json=as_json)

    except FileNotFoundError as e:
        print_error(str(e))
        sys.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.option("--vault", type=click.Path(exists=True), help="Path to vault root")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed progress")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def reindex(vault, yes, verbose, as_json):
    """Clear and rebuild vector index."""
    from .output import print_index_result, print_error, print_warning

    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    try:
        client = ObsidianRAG(vault_path=vault)

        if not yes and not as_json:
            print_warning(f"This will delete and rebuild the index for: {client.vault_config.name}")
            if not click.confirm("Continue?"):
                console.print("Cancelled.")
                return

        if not as_json:
            console.print(f"Rebuilding index for vault: [cyan]{client.vault_config.name}[/]")

        result = client.reindex_vault()
        print_index_result(result, as_json=as_json)

    except FileNotFoundError as e:
        print_error(str(e))
        sys.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        if verbose:
            logger.exception("Detailed error:")
        sys.exit(1)


if __name__ == "__main__":
    cli()
