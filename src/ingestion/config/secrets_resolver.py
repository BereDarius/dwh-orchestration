"""Secrets resolution from environment variables."""

import os
import re
from typing import Any

from ingestion.config.models import SecretsConfig


class SecretsResolver:
    """Resolves secrets from environment variables."""

    def __init__(self, secrets_config: SecretsConfig) -> None:
        """
        Initialize secrets resolver.

        Args:
            secrets_config: Secrets configuration
        """
        self.secrets_config = secrets_config
        self._cache: dict[str, str] = {}

    def get_secret(self, secret_key: str) -> str:
        """
        Get secret value from environment variables.

        Args:
            secret_key: Key to look up in environment variables

        Returns:
            str: Secret value

        Raises:
            ValueError: If secret is not found or invalid
        """
        # Check cache first
        if secret_key in self._cache:
            return self._cache[secret_key]

        # Get from environment
        value = os.getenv(secret_key)

        if value is None:
            if secret_key in self.secrets_config.secrets:
                secret_info = self.secrets_config.secrets[secret_key]
                if secret_info.required:
                    raise ValueError(
                        f"Required secret '{secret_key}' not found in environment variables. "
                        f"Description: {secret_info.description}"
                    )
            else:
                raise ValueError(f"Secret '{secret_key}' not defined in secrets mapping")

            # Return empty string for non-required secrets
            return ""

        # Validate pattern if defined
        if secret_key in self.secrets_config.validation.patterns:
            pattern = self.secrets_config.validation.patterns[secret_key]
            if not re.match(pattern, value):
                raise ValueError(
                    f"Secret '{secret_key}' does not match required pattern: {pattern}"
                )

        # Cache and return
        self._cache[secret_key] = value
        return value

    def resolve_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively resolve secrets in a dictionary.

        Looks for keys ending in '_secret_key' and resolves them.

        Args:
            data: Dictionary potentially containing secret keys

        Returns:
            Dict with resolved secrets
        """
        resolved: dict[str, Any] = {}

        for key, value in data.items():
            if isinstance(value, dict):
                resolved[key] = self.resolve_dict(value)  # type: ignore[arg-type]
            elif isinstance(value, list):
                result_list: list[Any] = []
                for item in value:  # type: ignore[misc]
                    if isinstance(item, dict):
                        result_list.append(self.resolve_dict(item))  # type: ignore[arg-type]
                    else:
                        result_list.append(item)
                resolved[key] = result_list
            elif isinstance(value, str) and key.endswith("_secret_key"):
                # This is a secret key reference - resolve it
                actual_key = key.replace("_secret_key", "")
                resolved[actual_key] = self.get_secret(value)
            else:
                resolved[key] = value

        return resolved

    def validate_required_secrets(self) -> None:
        """
        Validate that all required secrets are available.

        Raises:
            ValueError: If any required secrets are missing
        """
        missing_secrets: list[str] = []

        for secret_key in self.secrets_config.validation.required_secrets:
            try:
                self.get_secret(secret_key)
            except ValueError:
                missing_secrets.append(secret_key)

        if missing_secrets:
            raise ValueError(
                f"Missing required secrets: {', '.join(missing_secrets)}. "
                "Please ensure all required environment variables are set."
            )

    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        self._cache.clear()
