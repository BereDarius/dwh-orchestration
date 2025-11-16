#!/usr/bin/env python3
"""
Example script demonstrating the YouTube API pipeline.

This script shows how to:
1. Load configuration from YAML files
2. Validate the configuration
3. Execute a pipeline
4. Handle the results

Usage:
    # Set environment and required secrets
    export ENVIRONMENT=dev
    export YOUTUBE_API_KEY_DEV=your_api_key_here
    export DATABRICKS_SERVER_HOSTNAME_DEV=your_hostname
    export DATABRICKS_HTTP_PATH_DEV=your_http_path
    export DATABRICKS_ACCESS_TOKEN_DEV=your_token

    # Run the example
    python examples/run_youtube_pipeline.py
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ingestion.config import ConfigLoader, ConfigValidator
from ingestion.config.models import Environment
from ingestion.utils.logging import setup_logging

console = Console()


def main() -> None:
    """Run the YouTube pipeline example."""
    # Load environment variables
    load_dotenv()

    # Setup logging
    setup_logging(level="INFO")

    # Get environment
    env_str = os.getenv("ENVIRONMENT", "dev")
    environment = Environment(env_str)

    console.print(
        Panel(
            f"[bold]YouTube API to Databricks Pipeline[/bold]\n"
            f"Environment: [cyan]{environment.value}[/cyan]",
            title="Data Ingestion Framework Example",
            border_style="blue",
        )
    )

    # Step 1: Load configuration
    console.print("\n[bold]Step 1:[/bold] Loading configuration...")

    try:
        loader = ConfigLoader(environment)

        # Load pipeline config
        pipeline_config = loader.load_pipeline_config("youtube_to_databricks.yaml")
        console.print(f"  ✓ Loaded pipeline: [green]{pipeline_config.name}[/green]")

        # Load source config
        source_config = loader.load_source_config(pipeline_config.source.config_file)
        console.print(
            f"  ✓ Loaded source: [green]{source_config.name}[/green] "
            f"({source_config.type.value})"
        )

        # Load destination config
        dest_config = loader.load_destination_config(pipeline_config.destination.config_file)
        console.print(
            f"  ✓ Loaded destination: [green]{dest_config.name}[/green] "
            f"({dest_config.type.value})"
        )

    except Exception as e:
        console.print(f"[bold red]✗ Configuration loading failed: {e}[/bold red]")
        sys.exit(1)

    # Step 2: Validate configuration
    console.print("\n[bold]Step 2:[/bold] Validating configuration...")

    try:
        results = ConfigValidator.validate_all(source_config, dest_config, pipeline_config)

        if ConfigValidator.has_errors(results):
            console.print("[bold red]✗ Validation failed:[/bold red]")
            for component, errors in results.items():
                if errors:
                    console.print(f"  {component}:")
                    for error in errors:
                        console.print(f"    • {error}")
            sys.exit(1)

        console.print("  ✓ All validations passed")

    except Exception as e:
        console.print(f"[bold red]✗ Validation failed: {e}[/bold red]")
        sys.exit(1)

    # Step 3: Check secrets
    console.print("\n[bold]Step 3:[/bold] Checking secrets...")

    try:
        if loader.secrets_resolver:
            loader.secrets_resolver.validate_required_secrets()
            console.print("  ✓ All required secrets available")
        else:
            console.print("  [yellow]⚠ No secrets configuration found[/yellow]")

    except ValueError as e:
        console.print(f"[bold red]✗ Missing secrets: {e}[/bold red]")
        sys.exit(1)

    # Step 4: Display configuration
    console.print("\n[bold]Step 4:[/bold] Configuration summary...")

    # Source resources table
    resources_table = Table(title="Source Resources")
    resources_table.add_column("Resource", style="cyan")
    resources_table.add_column("Endpoint", style="white")
    resources_table.add_column("Incremental", style="green")

    for resource in source_config.resources:
        incremental = "✓" if resource.incremental and resource.incremental.enabled else "✗"
        resources_table.add_row(
            resource.name,
            resource.endpoint,
            incremental,
        )

    console.print(resources_table)

    # Pipeline info table
    pipeline_table = Table(title="Pipeline Configuration")
    pipeline_table.add_column("Setting", style="cyan")
    pipeline_table.add_column("Value", style="green")

    pipeline_table.add_row("Pipeline Name", pipeline_config.name)
    pipeline_table.add_row("Dataset", pipeline_config.destination.dataset_name)
    pipeline_table.add_row("Schedule", pipeline_config.schedule.cron)
    pipeline_table.add_row("Enabled", "✓" if pipeline_config.schedule.enabled else "✗")
    pipeline_table.add_row("Max Retries", str(pipeline_config.execution.retries))

    console.print(pipeline_table)

    # Step 5: Execute pipeline (optional - comment out if you don't want to run it)
    console.print("\n[bold]Step 5:[/bold] Execute pipeline...")

    # Uncomment the following lines to actually run the pipeline:
    """
    try:
        executor = PipelineExecutor()

        console.print("  Running pipeline (this may take a few minutes)...")
        result = executor.execute_pipeline_with_retry("youtube_to_databricks")

        if result.success:
            console.print("\n[bold green]✓ Pipeline completed successfully![/bold green]")

            # Show metrics
            metrics_table = Table(title="Pipeline Metrics")
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="green")

            metrics_table.add_row("Duration", f"{result.duration_seconds:.2f}s")
            metrics_table.add_row("Rows Processed", str(result.rows_processed))

            for key, value in result.metrics.items():
                if key not in ["row_counts", "total_rows"]:
                    metrics_table.add_row(key, str(value))

            console.print(metrics_table)
        else:
            console.print(f"[bold red]✗ Pipeline failed: {result.error}[/bold red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]✗ Execution failed: {e}[/bold red]")
        sys.exit(1)
    """

    console.print("\n[yellow]ℹ Pipeline execution is commented out in the example.[/yellow]")
    console.print(
        "[yellow]  Uncomment the execution code in examples/run_youtube_pipeline.py "
        "to actually run the pipeline.[/yellow]"
    )

    console.print("\n[bold green]✓ Example completed successfully![/bold green]")
    console.print(
        "\n[bold]Next steps:[/bold]\n"
        "  1. Set your environment variables (see .env.dev.example)\n"
        "  2. Uncomment the execution code above to run the pipeline\n"
        "  3. Or use the CLI: [cyan]ingestion run --pipeline youtube_to_databricks[/cyan]\n"
    )


if __name__ == "__main__":
    main()
