#!/usr/bin/env python3
"""
Quick start script to verify the installation and setup.

This script:
1. Checks Python version
2. Verifies dependencies are installed
3. Validates configuration files
4. Checks secrets availability
5. Shows next steps

Usage:
    python quickstart.py
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def check_python_version() -> bool:
    """Check if Python version is compatible."""
    print("Checking Python version...")
    version = sys.version_info

    if version.major == 3 and version.minor >= 10:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ✗ Python {version.major}.{version.minor}.{version.micro}")
        print("  ✗ Python 3.10 or higher is required")
        return False


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    print("\nChecking dependencies...")

    required = [
        ("dlt", "DLT"),
        ("pydantic", "Pydantic"),
        ("yaml", "PyYAML"),
        ("click", "Click"),
        ("rich", "Rich"),
        ("dotenv", "python-dotenv"),
    ]

    all_ok = True

    for module, name in required:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} not found")
            all_ok = False

    if not all_ok:
        print("\n  Run: pip install -r requirements.txt")

    return all_ok


def check_configuration() -> bool:
    """Check if configuration files exist."""
    print("\nChecking configuration files...")

    config_dir = Path("config")

    required_files = [
        "sources/youtube_api.yaml",
        "destinations/databricks.yaml",
        "pipelines/youtube_to_databricks.yaml",
        "secrets_mapping.yaml",
    ]

    all_ok = True

    for file in required_files:
        path = config_dir / file
        if path.exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} not found")
            all_ok = False

    return all_ok


def check_environment() -> bool:
    """Check if environment variables are set."""
    print("\nChecking environment variables...")

    # Check if .env file exists
    env_file = Path(".env.dev")
    env_example = Path(".env.dev.example")

    if env_file.exists():
        print("  ✓ .env.dev exists")

        # Load it
        from dotenv import load_dotenv

        load_dotenv(env_file)
    else:
        print("  ⚠ .env.dev not found")
        if env_example.exists():
            print("    Copy .env.dev.example to .env.dev and fill in your values")
        return False

    # Check required secrets
    required_secrets = [
        "YOUTUBE_API_KEY_DEV",
        "DATABRICKS_HOST_DEV",
        "DATABRICKS_HTTP_PATH_DEV",
        "DATABRICKS_TOKEN_DEV",
    ]

    all_ok = True

    for secret in required_secrets:
        value = os.getenv(secret)
        if value and value != "your_value_here":
            print(f"  ✓ {secret}")
        else:
            print(f"  ✗ {secret} not set")
            all_ok = False

    return all_ok


def validate_configs() -> bool:
    """Validate configuration using the framework."""
    print("\nValidating configurations...")

    try:
        from ingestion.config import ConfigLoader, ConfigValidator
        from ingestion.config.models import Environment

        loader = ConfigLoader(Environment.DEV)

        # Discover all configs
        all_configs = loader.discover_all_configs()
        sources = all_configs["sources"]
        destinations = all_configs["destinations"]
        pipelines = all_configs["pipelines"]

        print(
            f"  Found {len(sources)} source(s), {len(destinations)} destination(s), {len(pipelines)} pipeline(s)"
        )

        if not pipelines:
            print("  ⚠ No pipelines found")
            return False

        # Validate all pipelines
        all_valid = True
        for pipeline_name, pipeline_config in pipelines.items():
            source_config = loader.load_source_config(pipeline_config.source.config_file)
            dest_config = loader.load_destination_config(pipeline_config.destination.config_file)

            results = ConfigValidator.validate_all(source_config, dest_config, pipeline_config)

            if ConfigValidator.has_errors(results):
                all_valid = False
                print(f"  ✗ Pipeline '{pipeline_name}' validation failed:")
                for _component, errors in results.items():
                    if errors:
                        for error in errors:
                            print(f"    • {error}")

        if all_valid:
            print("  ✓ All configurations valid")

        return all_valid

    except Exception as e:
        print(f"  ✗ Validation failed: {e}")
        return False


def show_next_steps() -> None:
    """Show next steps to the user."""
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)

    print("\n1. Review your configuration:")
    print("   - config/sources/youtube_api.yaml")
    print("   - config/destinations/databricks.yaml")
    print("   - config/pipelines/youtube_to_databricks.yaml")

    print("\n2. Set your environment variables in .env.dev:")
    print("   - YOUTUBE_API_KEY_DEV")
    print("   - DATABRICKS_SERVER_HOSTNAME_DEV")
    print("   - DATABRICKS_HTTP_PATH_DEV")
    print("   - DATABRICKS_ACCESS_TOKEN_DEV")

    print("\n3. Try the example:")
    print("   python examples/run_youtube_pipeline.py")

    print("\n4. Use the CLI:")
    print("   ingestion list-pipelines --env dev")
    print("   ingestion validate --pipeline youtube_to_databricks --env dev")
    print("   ingestion run --pipeline youtube_to_databricks --env dev")

    print("\n5. Read the documentation:")
    print("   cat README.md")

    print("\n" + "=" * 60)


def main() -> None:
    """Run all checks."""
    print("=" * 60)
    print("DATA INGESTION FRAMEWORK - QUICK START")
    print("=" * 60)

    checks = [
        ("Python version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Configuration files", check_configuration),
        ("Environment variables", check_environment),
    ]

    all_passed = True

    for _name, check_func in checks:
        if not check_func():
            all_passed = False

    # Only validate if other checks passed
    if all_passed:
        validate_configs()

    print("\n" + "=" * 60)

    if all_passed:
        print("✓ ALL CHECKS PASSED!")
        print("=" * 60)
        show_next_steps()
    else:
        print("✗ SOME CHECKS FAILED")
        print("=" * 60)
        print("\nPlease fix the issues above and run this script again.")
        print("\nFor help, see:")
        print("  - README.md")
        print("  - .env.dev.example")
        sys.exit(1)


if __name__ == "__main__":
    main()
