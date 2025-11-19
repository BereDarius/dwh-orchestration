#!/usr/bin/env python3
"""
Example demonstrating dynamic configuration discovery.

This script shows how the framework automatically discovers and loads
all YAML configurations without hardcoding filenames.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.table import Table

from ingestion.config import ConfigLoader
from ingestion.config.models import Environment

console = Console()


def main() -> None:
    """Demonstrate dynamic configuration discovery."""
    console.print(
        "\n[bold blue]Dynamic Configuration Discovery Example[/bold blue]\n",
        style="bold",
    )

    # Initialize loader for dev environment
    loader = ConfigLoader(Environment.DEV)

    # Discover all configurations
    console.print("[bold]Step 1:[/bold] Discovering all configurations...\n")

    all_configs = loader.discover_all_configs()

    # Show sources
    sources = all_configs["sources"]
    console.print(f"[cyan]Found {len(sources)} source(s):[/cyan]")
    for name in sources.keys():
        console.print(f"  • {name}")

    # Show destinations
    destinations = all_configs["destinations"]
    console.print(f"\n[cyan]Found {len(destinations)} destination(s):[/cyan]")
    for name in destinations.keys():
        console.print(f"  • {name}")

    # Show pipelines
    pipelines = all_configs["pipelines"]
    console.print(f"\n[cyan]Found {len(pipelines)} pipeline(s):[/cyan]")
    for name in pipelines.keys():
        console.print(f"  • {name}")

    # Detailed pipeline information
    console.print("\n[bold]Step 2:[/bold] Pipeline details...\n")

    if pipelines:
        pipeline_table = Table(title="Available Pipelines")
        pipeline_table.add_column("Name", style="cyan")
        pipeline_table.add_column("Source", style="green")
        pipeline_table.add_column("Destination", style="blue")
        pipeline_table.add_column("Resources", style="white")
        pipeline_table.add_column("Schedule", style="yellow")

        for name, config in pipelines.items():
            resources = ", ".join(config.source.resources)
            pipeline_table.add_row(
                name,
                config.source.config_file.replace(".yaml", ""),
                config.destination.config_file.replace(".yaml", ""),
                resources,
                config.schedule.cron,
            )

        console.print(pipeline_table)
    else:
        console.print("[yellow]No pipelines configured[/yellow]")

    # Show source details
    console.print("\n[bold]Step 3:[/bold] Source details...\n")

    if sources:
        source_table = Table(title="Available Sources")
        source_table.add_column("Name", style="cyan")
        source_table.add_column("Type", style="green")
        source_table.add_column("Resources", style="white")
        source_table.add_column("Incremental", style="blue")

        for name, config in sources.items():
            resource_names = ", ".join([r.name for r in config.resources])
            incremental_count = sum(
                1 for r in config.resources if r.incremental and r.incremental.enabled
            )
            source_table.add_row(
                name,
                config.type.value,
                resource_names,
                f"{incremental_count}/{len(config.resources)}",
            )

        console.print(source_table)
    else:
        console.print("[yellow]No sources configured[/yellow]")

    # Adding a new configuration example
    console.print("\n[bold]Step 4:[/bold] How to add a new pipeline...\n")

    console.print("[green]To add a new pipeline:[/green]")
    console.print("  1. Create a YAML file in config/pipelines/")
    console.print("  2. Define your source, destination, and schedule")
    console.print("  3. Run this script again - it will be automatically discovered!")
    console.print("\n[green]Example:[/green] Create config/pipelines/my_new_pipeline.yaml")

    console.print("\n[bold green]✓ Dynamic discovery complete![/bold green]")
    console.print("\n[dim]All configurations are loaded dynamically from YAML files.[/dim]")
    console.print("[dim]No code changes needed to add/remove pipelines![/dim]\n")


if __name__ == "__main__":
    main()
