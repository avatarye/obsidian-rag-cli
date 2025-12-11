"""Initialize vault configuration."""

import click
from pathlib import Path
import toml
from rich.prompt import Prompt, Confirm

from ..output import console, print_success, print_error, print_info


def create_default_vault_config(vault_path: Path, name: str, dirs: list) -> None:
    """Create default .orag.toml file."""
    config_file = vault_path / ".orag.toml"

    if config_file.exists():
        raise FileExistsError(f".orag.toml already exists at {vault_path}")

    config_data = {
        "vault": {
            "name": name,
            "dirs": dirs,
        },
        "storage": {
            "vector_store": ".vector_store",
        },
    }

    with open(config_file, "w") as f:
        toml.dump(config_data, f)

    # Write with comments for clarity
    config_content = f"""# Obsidian RAG Vault Configuration

[vault]
# Vault name (used for vector store collection)
name = "{name}"

# Directories to index (relative paths from vault root)
# All .md files in these directories will be indexed
dirs = {dirs}

[storage]
# Vector store location (relative to vault root)
vector_store = ".vector_store"
"""
    config_file.write_text(config_content)


@click.command()
@click.option("--name", help="Vault name (defaults to directory name)")
@click.option("--dirs", help="Comma-separated list of directories to index (default: .)")
@click.option("--force", is_flag=True, help="Overwrite existing .orag.toml")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode with prompts")
def init(name, dirs, force, interactive):
    """Initialize vault configuration (.orag.toml)."""
    vault_path = Path.cwd()

    # Check if config already exists
    config_file = vault_path / ".orag.toml"
    if config_file.exists() and not force:
        print_error(f".orag.toml already exists at {vault_path}")
        console.print("\n💡 [dim]Use --force to overwrite, or edit the file directly[/]")
        return

    # Interactive mode
    if interactive:
        console.print("\n[bold cyan]Initialize Obsidian RAG Vault[/]\n")

        # Get vault name
        default_name = vault_path.name
        vault_name = Prompt.ask(
            "Vault name",
            default=default_name
        )

        # Get directories
        default_dirs = "."
        dirs_input = Prompt.ask(
            "Directories to index (comma-separated)",
            default=default_dirs
        )
        dirs_list = [d.strip() for d in dirs_input.split(",")]

        # Confirm
        console.print(f"\n[dim]Creating .orag.toml with:[/]")
        console.print(f"  • Name: [cyan]{vault_name}[/]")
        console.print(f"  • Directories: [cyan]{', '.join(dirs_list)}[/]")

        if not Confirm.ask("\nContinue?", default=True):
            console.print("Cancelled.")
            return
    else:
        # Non-interactive mode
        vault_name = name or vault_path.name
        dirs_list = [d.strip() for d in dirs.split(",")] if dirs else ["."]

    # Create config
    try:
        if force and config_file.exists():
            config_file.unlink()
            print_info(f"Removed existing .orag.toml")

        create_default_vault_config(vault_path, vault_name, dirs_list)
        print_success(f"Created .orag.toml at {vault_path}")

        console.print("\n[dim]Next steps:[/]")
        console.print("  1. Edit .orag.toml to customize settings (optional)")
        console.print("  2. Run [cyan]orag index[/] to build the vector database\n")

    except Exception as e:
        print_error(f"Error creating config: {e}")
