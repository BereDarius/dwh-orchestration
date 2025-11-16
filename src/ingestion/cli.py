"""CLI for the data ingestion framework."""

import os
import sys

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from ingestion.config import ConfigLoader, ConfigValidator
from ingestion.config.models import Environment
from ingestion.pipelines import PipelineExecutor
from ingestion.utils.logging import setup_logging

console = Console()


@click.group()
@click.option(
    "--env",
    type=click.Choice(["dev", "stage", "prod"]),
    default="dev",
    help="Environment to use",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Logging level",
)
@click.pass_context
def cli(ctx: click.Context, env: str, log_level: str) -> None:
    """Data Ingestion Framework CLI."""
    # Load environment variables
    load_dotenv()

    # Set environment
    os.environ["ENVIRONMENT"] = env

    # Setup logging
    setup_logging(level=log_level)

    # Store in context
    ctx.ensure_object(dict)
    ctx.obj["environment"] = Environment(env)
    ctx.obj["log_level"] = log_level


@cli.command()
@click.option(
    "--pipeline",
    required=True,
    help="Name of the pipeline to run",
)
@click.option(
    "--retry/--no-retry",
    default=True,
    help="Enable retry on failure",
)
@click.pass_context
def run(ctx: click.Context, pipeline: str, retry: bool) -> None:
    """Run a data ingestion pipeline."""
    environment = ctx.obj["environment"]

    console.print(f"\n[bold blue]Running pipeline: {pipeline}[/bold blue]")
    console.print(f"Environment: [green]{environment.value}[/green]\n")

    try:
        # Create executor
        executor = PipelineExecutor()

        # Execute pipeline
        if retry:
            result = executor.execute_pipeline_with_retry(pipeline)
        else:
            result = executor.execute_pipeline(pipeline)

        # Display results
        if result.success:
            console.print("[bold green]✓ Pipeline completed successfully![/bold green]\n")

            # Show metrics
            table = Table(title="Pipeline Metrics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Duration", f"{result.duration_seconds:.2f}s")
            table.add_row("Rows Processed", str(result.rows_processed))

            for key, value in result.metrics.items():
                if key not in ["row_counts", "total_rows"]:
                    table.add_row(key, str(value))

            console.print(table)
        else:
            console.print(f"[bold red]✗ Pipeline failed: {result.error}[/bold red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def list_pipelines(ctx: click.Context) -> None:
    """List all available pipelines."""
    environment = ctx.obj["environment"]

    console.print(f"\n[bold blue]Available pipelines in {environment.value}:[/bold blue]\n")

    try:
        loader = ConfigLoader(environment)
        pipelines = loader.load_all_pipelines()

        if not pipelines:
            console.print("[yellow]No pipelines found[/yellow]")
            return

        table = Table()
        table.add_column("Pipeline", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Schedule", style="green")
        table.add_column("Enabled", style="yellow")

        for name, config in pipelines.items():
            enabled = "✓" if config.schedule.enabled else "✗"
            table.add_row(
                name,
                config.description or "",
                config.schedule.cron,
                enabled,
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--pipeline",
    required=True,
    help="Name of the pipeline to validate",
)
@click.pass_context
def validate(ctx: click.Context, pipeline: str) -> None:
    """Validate a pipeline configuration."""
    environment = ctx.obj["environment"]

    console.print(f"\n[bold blue]Validating pipeline: {pipeline}[/bold blue]\n")

    try:
        loader = ConfigLoader(environment)

        # Load configs
        pipeline_config = loader.load_pipeline_config(f"{pipeline}.yaml")
        source_config = loader.load_source_config(pipeline_config.source.config_file)
        dest_config = loader.load_destination_config(pipeline_config.destination.config_file)

        # Validate
        results = ConfigValidator.validate_all(source_config, dest_config, pipeline_config)

        # Display results
        has_errors = ConfigValidator.has_errors(results)

        if not has_errors:
            console.print("[bold green]✓ All validations passed![/bold green]")
        else:
            console.print("[bold red]✗ Validation errors found:[/bold red]\n")

            for component, errors in results.items():
                if errors:
                    console.print(f"[yellow]{component.upper()}:[/yellow]")
                    for error in errors:
                        console.print(f"  • {error}")

            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def check_secrets(ctx: click.Context) -> None:
    """Check if all required secrets are available."""
    environment = ctx.obj["environment"]

    console.print(f"\n[bold blue]Checking secrets for {environment.value}:[/bold blue]\n")

    try:
        loader = ConfigLoader(environment)

        if not loader.secrets_resolver:
            console.print("[yellow]No secrets configuration found[/yellow]")
            return

        # Validate secrets
        loader.secrets_resolver.validate_required_secrets()

        console.print("[bold green]✓ All required secrets are available![/bold green]")

    except ValueError as e:
        console.print(f"[bold red]✗ Missing secrets: {e}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def list_sources(ctx: click.Context) -> None:
    """List all available sources."""
    environment = ctx.obj["environment"]

    console.print(f"\n[bold blue]Available sources in {environment.value}:[/bold blue]\n")

    try:
        loader = ConfigLoader(environment)
        sources = loader.load_all_sources()

        if not sources:
            console.print("[yellow]No sources found[/yellow]")
            return

        table = Table()
        table.add_column("Source", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Resources", style="white")
        table.add_column("Base URL", style="blue")

        for name, config in sources.items():
            resources = ", ".join([r.name for r in config.resources])
            base_url = getattr(config.connection, "base_url", "N/A")
            table.add_row(
                name,
                config.type.value,
                resources,
                base_url,
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def list_destinations(ctx: click.Context) -> None:
    """List all available destinations."""
    environment = ctx.obj["environment"]

    console.print(f"\n[bold blue]Available destinations in {environment.value}:[/bold blue]\n")

    try:
        loader = ConfigLoader(environment)
        destinations = loader.load_all_destinations()

        if not destinations:
            console.print("[yellow]No destinations found[/yellow]")
            return

        table = Table()
        table.add_column("Destination", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Catalog/Database", style="white")
        table.add_column("Schema", style="blue")

        for name, config in destinations.items():
            catalog = getattr(config.connection, "catalog", "N/A")
            schema = getattr(config.connection, "schema", "N/A")
            table.add_row(
                name,
                config.type.value,
                catalog,
                schema,
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def discover(ctx: click.Context) -> None:
    """Discover all configurations in the current environment."""
    environment = ctx.obj["environment"]

    console.print(
        f"\n[bold blue]Discovering all configurations in {environment.value}:[/bold blue]\n"
    )

    try:
        loader = ConfigLoader(environment)
        all_configs = loader.discover_all_configs()

        # Sources
        sources = all_configs["sources"]
        console.print(f"[cyan]Sources:[/cyan] {len(sources)}")
        for name in sources.keys():
            console.print(f"  • {name}")

        # Destinations
        destinations = all_configs["destinations"]
        console.print(f"\n[cyan]Destinations:[/cyan] {len(destinations)}")
        for name in destinations.keys():
            console.print(f"  • {name}")

        # Pipelines
        pipelines = all_configs["pipelines"]
        console.print(f"\n[cyan]Pipelines:[/cyan] {len(pipelines)}")
        for name in pipelines.keys():
            console.print(f"  • {name}")

        console.print(
            f"\n[bold green]✓ Found {len(sources)} sources, "
            f"{len(destinations)} destinations, "
            f"and {len(pipelines)} pipelines[/bold green]"
        )

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
