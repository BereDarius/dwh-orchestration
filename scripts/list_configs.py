#!/usr/bin/env python3
"""List all available configurations in the current environment."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestion.config import ConfigLoader
from ingestion.config.models import Environment


def list_all_configs(env: str) -> None:
    """
    List all configurations for an environment.

    Args:
        env: Environment name (dev, stage, prod)
    """
    try:
        environment = Environment(env)
    except ValueError:
        print(f"❌ Invalid environment: {env}")
        print("   Must be one of: dev, stage, prod")
        sys.exit(1)

    print(f"📋 Listing all configurations for {env} environment\n")

    loader = ConfigLoader(environment)

    # Discover all configurations
    try:
        all_configs = loader.discover_all_configs()
    except Exception as e:
        print(f"❌ Error discovering configurations: {e}")
        sys.exit(1)

    # List sources
    sources = all_configs["sources"]
    print(f"🔌 SOURCES ({len(sources)})")
    print("=" * 60)
    if sources:
        for name, config in sources.items():
            print(f"\n📦 {name}")
            print(f"   Type: {config.type.value}")
            if hasattr(config.connection, "base_url"):
                print(f"   Base URL: {config.connection.base_url}")
            print(f"   Resources ({len(config.resources)}):")
            for resource in config.resources:
                incremental = "✓" if resource.incremental and resource.incremental.enabled else "✗"
                print(f"      • {resource.name} (incremental: {incremental})")
    else:
        print("   No sources found")

    # List destinations
    destinations = all_configs["destinations"]
    print(f"\n\n🎯 DESTINATIONS ({len(destinations)})")
    print("=" * 60)
    if destinations:
        for name, config in destinations.items():
            print(f"\n📦 {name}")
            print(f"   Type: {config.type.value}")
            if hasattr(config.connection, "catalog"):
                print(f"   Catalog: {config.connection.catalog}")
            if hasattr(config.connection, "schema"):
                print(f"   Schema: {config.connection.schema}")
    else:
        print("   No destinations found")

    # List pipelines
    pipelines = all_configs["pipelines"]
    print(f"\n\n🔄 PIPELINES ({len(pipelines)})")
    print("=" * 60)
    if pipelines:
        for name, config in pipelines.items():
            print(f"\n📦 {name}")
            if config.description:
                print(f"   Description: {config.description}")
            print(f"   Source: {config.source.config_file}")
            print(f"   Destination: {config.destination.config_file}")
            print(f"   Dataset: {config.destination.dataset_name}")
            print(f"   Schedule: {config.schedule.cron}")
            print(f"   Enabled: {'✓' if config.schedule.enabled else '✗'}")
            print(f"   Resources: {', '.join(config.source.resources)}")
    else:
        print("   No pipelines found")

    # Summary
    print("\n" + "=" * 60)
    print(
        f"✓ Total: {len(sources)} sources, {len(destinations)} destinations, "
        f"{len(pipelines)} pipelines"
    )
    print("=" * 60)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="List all available configurations for an environment"
    )
    parser.add_argument(
        "--env",
        type=str,
        default="dev",
        choices=["dev", "stage", "prod"],
        help="Environment to list (default: dev)",
    )

    args = parser.parse_args()
    list_all_configs(args.env)


if __name__ == "__main__":
    main()
