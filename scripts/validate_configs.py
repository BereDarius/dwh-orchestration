#!/usr/bin/env python3
"""Validate configuration files for a specific environment."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestion.config import ConfigLoader, ConfigValidator
from ingestion.config.models import Environment


def validate_environment(env: str) -> bool:
    """
    Validate all configurations for an environment.

    Args:
        env: Environment name (dev, stage, prod)

    Returns:
        True if all validations pass, False otherwise
    """
    try:
        environment = Environment(env)
    except ValueError:
        print(f"❌ Invalid environment: {env}")
        print("   Must be one of: dev, stage, prod")
        return False

    print(f"🔍 Validating configurations for {env} environment...\n")

    loader = ConfigLoader(environment)
    all_valid = True

    # Discover all configurations
    print("📦 Discovering configurations...")
    try:
        all_configs = loader.discover_all_configs()
        sources = all_configs["sources"]
        destinations = all_configs["destinations"]
        pipelines = all_configs["pipelines"]

        print(f"   ✓ Found {len(sources)} source(s)")
        print(f"   ✓ Found {len(destinations)} destination(s)")
        print(f"   ✓ Found {len(pipelines)} pipeline(s)")
    except Exception as e:
        print(f"❌ Error discovering configurations: {e}")
        return False

    # Validate sources
    if sources:
        print("\n🔌 Validating sources...")
        for source_name, source_config in sources.items():
            try:
                source_errors = ConfigValidator.validate_source_config(source_config)
                if source_errors:
                    all_valid = False
                    print(f"   ❌ {source_name}:")
                    for error in source_errors:
                        print(f"      - {error}")
                else:
                    print(f"   ✓ {source_name}")
            except Exception as e:
                all_valid = False
                print(f"   ❌ {source_name}: {e}")

    # Validate destinations
    if destinations:
        print("\n🎯 Validating destinations...")
        for dest_name, dest_config in destinations.items():
            try:
                dest_errors = ConfigValidator.validate_destination_config(dest_config)
                if dest_errors:
                    all_valid = False
                    print(f"   ❌ {dest_name}:")
                    for error in dest_errors:
                        print(f"      - {error}")
                else:
                    print(f"   ✓ {dest_name}")
            except Exception as e:
                all_valid = False
                print(f"   ❌ {dest_name}: {e}")

    # Validate each pipeline
    if pipelines:
        print("\n🔄 Validating pipelines...")
        for pipeline_name, pipeline_config in pipelines.items():
            print(f"\n   📋 Pipeline: {pipeline_name}")

            try:
                # Load source config
                source_config = loader.load_source_config(pipeline_config.source.config_file)
                print(f"      ✓ Source: {source_config.name}")

                # Load destination config
                dest_config = loader.load_destination_config(
                    pipeline_config.destination.config_file
                )
                print(f"      ✓ Destination: {dest_config.name}")

                # Validate all configs together
                validation_results = ConfigValidator.validate_all(
                    source_config, dest_config, pipeline_config
                )

                # Check for errors
                has_errors = ConfigValidator.has_errors(validation_results)

                if has_errors:
                    all_valid = False
                    print("      ❌ Validation errors:")

                    for component, errors in validation_results.items():
                        if errors:
                            print(f"\n      {component.upper()}:")
                            for error in errors:
                                print(f"         - {error}")
                else:
                    print("      ✓ All validations passed")

            except Exception as e:
                all_valid = False
                print(f"      ❌ Error: {e}")

    if not sources and not destinations and not pipelines:
        print("⚠️  No configurations found!")
        return False

    print("\n" + "=" * 60)
    if all_valid:
        print("✅ All configurations are valid!")
        return True
    else:
        print("❌ Some configurations have errors. Please fix them.")
        return False


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate configuration files for an environment")
    parser.add_argument(
        "--env",
        type=str,
        required=True,
        choices=["dev", "stage", "prod"],
        help="Environment to validate (dev, stage, or prod)",
    )

    args = parser.parse_args()

    success = validate_environment(args.env)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
