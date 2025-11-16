#!/usr/bin/env python3
"""Validate that all required secrets are available."""

import argparse
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestion.config import ConfigLoader
from ingestion.config.models import Environment


def validate_secrets(env: str) -> bool:
    """
    Validate that all required secrets are available.

    Args:
        env: Environment name (dev, stage, prod)

    Returns:
        True if all secrets are available, False otherwise
    """
    try:
        environment = Environment(env)
    except ValueError:
        print(f"❌ Invalid environment: {env}")
        print("   Must be one of: dev, stage, prod")
        return False

    print(f"🔐 Validating secrets for {env} environment...\n")

    # Load configuration
    loader = ConfigLoader(environment)

    if not loader.secrets_resolver:
        print("❌ No secrets configuration found")
        return False

    try:
        # Validate all required secrets
        loader.secrets_resolver.validate_required_secrets()
        print("✅ All required secrets are available!\n")

        # Show which secrets were found
        secrets_config = loader.load_secrets_config()
        print("Found secrets:")
        for secret_key, secret_info in secrets_config.secrets.items():
            value = os.getenv(secret_key)
            if value:
                masked_value = value[:4] + "*" * (len(value) - 4) if len(value) > 4 else "****"
                print(f"   ✓ {secret_key}: {masked_value}")
            else:
                if secret_info.required:
                    print(f"   ❌ {secret_key}: MISSING (required)")
                else:
                    print(f"   ⚠️  {secret_key}: Not set (optional)")

        return True

    except ValueError as e:
        print(f"❌ Validation failed: {e}\n")

        # Show which secrets are missing
        secrets_config = loader.load_secrets_config()
        print("Secret status:")
        for secret_key, secret_info in secrets_config.secrets.items():
            value = os.getenv(secret_key)
            if value:
                print(f"   ✓ {secret_key}")
            else:
                status = "REQUIRED" if secret_info.required else "optional"
                print(f"   ❌ {secret_key} ({status})")
                print(f"      {secret_info.description}")

        return False


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate secrets for an environment")
    parser.add_argument(
        "--env",
        type=str,
        required=True,
        choices=["dev", "stage", "prod"],
        help="Environment to validate (dev, stage, or prod)",
    )

    args = parser.parse_args()

    # Load environment variables from .env file
    from dotenv import load_dotenv

    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"📄 Loaded environment from {env_file}\n")
    else:
        print("⚠️  No .env file found. Using system environment variables only.\n")

    success = validate_secrets(args.env)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
