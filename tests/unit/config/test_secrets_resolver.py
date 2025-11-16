"""Unit tests for secrets resolver."""

from typing import Any

import pytest
from _pytest.monkeypatch import MonkeyPatch

from ingestion.config.models import Environment, SecretMapping, SecretsConfig, SecretsValidation
from ingestion.config.secrets_resolver import SecretsResolver


class TestSecretsResolver:
    """Tests for SecretsResolver class."""

    @pytest.fixture
    def secrets_config(self) -> SecretsConfig:
        """Create a sample secrets config."""
        return SecretsConfig(
            environment=Environment.DEV,
            secrets={
                "TEST_API_KEY": SecretMapping(
                    github_secret="TEST_API_KEY", description="Test API key", required=True
                ),
                "OPTIONAL_KEY": SecretMapping(
                    github_secret="OPTIONAL_KEY", description="Optional key", required=False
                ),
            },
            validation=SecretsValidation(
                required_secrets=["TEST_API_KEY"], patterns={"TEST_API_KEY": r"^[a-zA-Z0-9_-]+$"}
            ),
        )

    def test_init(self, secrets_config: SecretsConfig) -> None:
        """Test SecretsResolver initialization."""
        resolver = SecretsResolver(secrets_config)
        assert resolver.secrets_config == secrets_config
        # Use type: ignore for accessing protected member in tests
        assert resolver._cache == {}  # type: ignore[attr-defined]

    def test_get_secret_from_env(
        self, secrets_config: SecretsConfig, monkeypatch: MonkeyPatch
    ) -> None:
        """Test getting secret from environment variables."""
        monkeypatch.setenv("TEST_API_KEY", "test-key-12345")
        resolver = SecretsResolver(secrets_config)

        value = resolver.get_secret("TEST_API_KEY")
        assert value == "test-key-12345"

    def test_get_secret_caching(
        self, secrets_config: SecretsConfig, monkeypatch: MonkeyPatch
    ) -> None:
        """Test secret caching."""
        monkeypatch.setenv("TEST_API_KEY", "test-key-12345")
        resolver = SecretsResolver(secrets_config)

        # First call
        value1 = resolver.get_secret("TEST_API_KEY")
        # Second call should use cache
        value2 = resolver.get_secret("TEST_API_KEY")

        assert value1 == value2
        # Use type: ignore for accessing protected member in tests
        assert "TEST_API_KEY" in resolver._cache  # type: ignore[attr-defined]

    def test_get_secret_required_missing(self, secrets_config: SecretsConfig) -> None:
        """Test getting required secret that is missing."""
        resolver = SecretsResolver(secrets_config)

        with pytest.raises(ValueError, match="Required secret"):
            resolver.get_secret("TEST_API_KEY")

    def test_get_secret_optional_missing(self, secrets_config: SecretsConfig) -> None:
        """Test getting optional secret that is missing."""
        resolver = SecretsResolver(secrets_config)

        # Should return empty string for optional secrets that are missing
        value = resolver.get_secret("OPTIONAL_KEY")
        assert value == ""
        # Empty strings for missing optional secrets are NOT cached
        assert "OPTIONAL_KEY" not in resolver._cache  # type: ignore[attr-defined]

    def test_get_secret_not_in_config(self, secrets_config: SecretsConfig) -> None:
        """Test getting secret not in config and not in environment."""
        resolver = SecretsResolver(secrets_config)

        # Should raise ValueError when secret is not in config and not in env
        with pytest.raises(ValueError, match="not defined in secrets mapping"):
            resolver.get_secret("UNKNOWN_KEY")

    def test_validate_secrets_all_present(
        self, secrets_config: SecretsConfig, monkeypatch: MonkeyPatch
    ) -> None:
        """Test validating when all required secrets are present."""
        monkeypatch.setenv("TEST_API_KEY", "test-key-12345")
        resolver = SecretsResolver(secrets_config)
        # Should not raise
        resolver.validate_required_secrets()

    def test_validate_secrets_missing_required(self, secrets_config: SecretsConfig) -> None:
        """Test validating when required secret is missing."""
        resolver = SecretsResolver(secrets_config)
        with pytest.raises(ValueError):
            resolver.validate_required_secrets()

    def test_get_secret_pattern_validation_success(
        self, secrets_config: SecretsConfig, monkeypatch: MonkeyPatch
    ) -> None:
        """Test secret value matches required pattern."""
        monkeypatch.setenv("TEST_API_KEY", "valid_key-123")
        resolver = SecretsResolver(secrets_config)

        value = resolver.get_secret("TEST_API_KEY")
        assert value == "valid_key-123"

    def test_get_secret_pattern_validation_failure(
        self, secrets_config: SecretsConfig, monkeypatch: MonkeyPatch
    ) -> None:
        """Test secret value fails pattern validation."""
        monkeypatch.setenv("TEST_API_KEY", "invalid key!")  # Contains space and !
        resolver = SecretsResolver(secrets_config)

        with pytest.raises(ValueError, match="does not match required pattern"):
            resolver.get_secret("TEST_API_KEY")

    def test_get_secret_no_pattern_validation(
        self, secrets_config: SecretsConfig, monkeypatch: MonkeyPatch
    ) -> None:
        """Test getting secret with no pattern validation defined."""
        monkeypatch.setenv("OPTIONAL_KEY", "any-value-works")
        resolver = SecretsResolver(secrets_config)

        # OPTIONAL_KEY has no pattern in validation, should pass
        value = resolver.get_secret("OPTIONAL_KEY")
        assert value == "any-value-works"
        # Should be cached
        assert resolver._cache.get("OPTIONAL_KEY") == "any-value-works"  # type: ignore[attr-defined]

    def test_resolve_dict_simple(
        self, secrets_config: SecretsConfig, monkeypatch: MonkeyPatch
    ) -> None:
        """Test resolving secrets in a simple dictionary."""
        monkeypatch.setenv("TEST_API_KEY", "resolved-key-123")
        resolver = SecretsResolver(secrets_config)

        data = {"api_key_secret_key": "TEST_API_KEY", "other_field": "value"}
        resolved = resolver.resolve_dict(data)

        assert resolved["api_key"] == "resolved-key-123"
        assert resolved["other_field"] == "value"
        assert "api_key_secret_key" not in resolved

    def test_resolve_dict_nested(
        self, secrets_config: SecretsConfig, monkeypatch: MonkeyPatch
    ) -> None:
        """Test resolving secrets in nested dictionaries."""
        monkeypatch.setenv("TEST_API_KEY", "nested-key-456")
        resolver = SecretsResolver(secrets_config)

        data: dict[str, Any] = {  # type: ignore[misc]
            "connection": {"token_secret_key": "TEST_API_KEY", "host": "localhost"},
            "name": "test",
        }
        resolved = resolver.resolve_dict(data)

        assert resolved["connection"]["token"] == "nested-key-456"
        assert resolved["connection"]["host"] == "localhost"
        assert resolved["name"] == "test"

    def test_resolve_dict_with_list(
        self, secrets_config: SecretsConfig, monkeypatch: MonkeyPatch
    ) -> None:
        """Test resolving secrets in dictionaries containing lists."""
        monkeypatch.setenv("TEST_API_KEY", "list-key-789")
        resolver = SecretsResolver(secrets_config)

        data: dict[str, Any] = {  # type: ignore[misc]
            "items": [
                {"key_secret_key": "TEST_API_KEY", "id": 1},
                {"key_secret_key": "TEST_API_KEY", "id": 2},
            ],
            "simple_list": [1, 2, 3],
        }
        resolved = resolver.resolve_dict(data)

        assert resolved["items"][0]["key"] == "list-key-789"
        assert resolved["items"][0]["id"] == 1
        assert resolved["items"][1]["key"] == "list-key-789"
        assert resolved["simple_list"] == [1, 2, 3]

    def test_clear_cache(self, secrets_config: SecretsConfig, monkeypatch: MonkeyPatch) -> None:
        """Test clearing the secrets cache."""
        monkeypatch.setenv("TEST_API_KEY", "cached-key")
        resolver = SecretsResolver(secrets_config)

        # Populate cache
        resolver.get_secret("TEST_API_KEY")
        assert "TEST_API_KEY" in resolver._cache  # type: ignore[attr-defined]

        # Clear cache
        resolver.clear_cache()
        assert resolver._cache == {}  # type: ignore[attr-defined]
