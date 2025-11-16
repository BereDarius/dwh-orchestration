#!/usr/bin/env python3
"""
Run the mock API to DuckDB pipeline locally.

This script demonstrates a complete data ingestion pipeline:
1. Fetches data from JSONPlaceholder (mock REST API)
2. Loads it into a local DuckDB database
3. No external credentials required!

Usage:
    python examples/run_mock_pipeline.py
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
    """Run the mock pipeline."""
    print("=" * 60)
    print("MOCK API TO DUCKDB PIPELINE")
    print("=" * 60)
    print()

    # Create pipeline factory
    print("Creating pipeline factory...")
    factory = PipelineFactory(environment=Environment.DEV)

    # Create executor
    print("Creating pipeline executor...")
    executor = PipelineExecutor(pipeline_factory=factory)

    # Execute pipeline
    print("Executing pipeline: mock_to_duckdb")
    print()
    result = executor.execute_pipeline("mock_to_duckdb")

    # Print results
    print()
    print("=" * 60)
    if result.success:
        print("✓ PIPELINE SUCCEEDED!")
        print("=" * 60)
        print()
        print(f"Duration: {result.duration_seconds:.2f} seconds")
        print(f"Rows processed: {result.rows_processed}")
        print("Database: data/local.duckdb")
        print("Dataset: mock_data")
        print()
        print("Tables created:")
        print("  - users")
        print("  - posts")
        print("  - comments")
        print()
        print("To query the data:")
        print("  1. Install DuckDB CLI: brew install duckdb")
        print("  2. Run: duckdb data/local.duckdb")
        print("  3. Query: SELECT * FROM mock_data.users LIMIT 5;")
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
