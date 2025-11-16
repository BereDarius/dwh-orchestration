#!/usr/bin/env python3
"""
Run the GitHub API to DuckDB pipeline.

This script demonstrates ingesting real-world data from GitHub's public API:
- Fetches repository data from a GitHub user (default: torvalds)
- Loads it into a local DuckDB database
- No authentication required for public data!

Usage:
    # Default (Linus Torvalds' repos)
    python examples/run_github_pipeline.py

    # Custom GitHub user
    python examples/run_github_pipeline.py --username your-username
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestion.config.models import Environment
from ingestion.pipelines.executor import PipelineExecutor
from ingestion.pipelines.factory import PipelineFactory
from ingestion.utils.logging import setup_logging

# Setup logging
setup_logging(level="INFO")


def main():
    """Run the GitHub pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest GitHub data to DuckDB")
    parser.add_argument(
        "--username",
        default="torvalds",
        help="GitHub username to fetch repos from (default: torvalds)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("GITHUB API TO DUCKDB PIPELINE")
    print("=" * 60)
    print(f"\nFetching repositories for: {args.username}")
    print()

    # Create pipeline factory
    print("Creating pipeline factory...")
    factory = PipelineFactory(environment=Environment.DEV)

    # Load pipeline config
    pipeline_config = factory.config_loader.load_pipeline_config("github_to_duckdb.yaml")

    # Override username parameter
    pipeline_config.source.params["username"] = args.username

    # Create executor
    print("Creating pipeline executor...")
    executor = PipelineExecutor(pipeline_factory=factory)

    # Execute pipeline
    print("Executing pipeline: github_to_duckdb")
    print()
    result = executor.execute_pipeline("github_to_duckdb", pipeline_config=pipeline_config)

    # Print results
    print()
    print("=" * 60)
    if result.success:
        print("✓ PIPELINE SUCCEEDED!")
        print("=" * 60)
        print()
        print(f"Duration: {result.duration_seconds:.2f} seconds")
        print(f"Rows processed: {result.rows_processed}")
        print("Database: github_to_duckdb.duckdb")
        print("Dataset: github_analytics")
        print()
        print("Tables created:")
        print("  - repos")
        print()
        print("To query the data:")
        print("  duckdb github_to_duckdb.duckdb")
        print()
        print("Example queries:")
        print("  SELECT name, stargazers_count, language FROM github_analytics.repos")
        print("  ORDER BY stargazers_count DESC LIMIT 10;")
        print()
        print("  SELECT language, COUNT(*) as repo_count")
        print("  FROM github_analytics.repos")
        print("  GROUP BY language ORDER BY repo_count DESC;")
        print()
    else:
        print("✗ PIPELINE FAILED!")
        print("=" * 60)
        print()
        print(f"Error: {result.error}")
        print()

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
