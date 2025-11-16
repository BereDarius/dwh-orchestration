"""Unit tests for RestApiSource."""

from unittest.mock import MagicMock, patch

import pytest

from ingestion.config.models import (
    AuthConfig,
    AuthType,
    ConnectionConfig,
    Environment,
    IncrementalConfig,
    ResourceConfig,
    SourceConfig,
    WriteDisposition,
)
from ingestion.sources.rest_api import RestApiSource


class TestRestApiSource:
    """Tests for RestApiSource class."""

    @pytest.fixture
    def basic_config(self) -> SourceConfig:
        """Create a basic REST API source configuration."""
        return SourceConfig(
            name="test_api",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(base_url="https://api.example.com"),
            resources=[
                ResourceConfig(
                    name="users",
                    endpoint="/users",
                    method="GET",
                    params={},
                ),
            ],
        )

    @pytest.fixture
    def auth_bearer_config(self) -> SourceConfig:
        """Create a REST API source configuration with bearer auth."""
        return SourceConfig(
            name="test_api_bearer",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(
                base_url="https://api.example.com",
                auth=AuthConfig(
                    type=AuthType.BEARER,
                    credentials_secret_key="API_TOKEN",
                ),
            ),
            resources=[ResourceConfig(name="users", endpoint="/users")],
        )

    @pytest.fixture
    def incremental_config(self) -> SourceConfig:
        """Create a REST API source configuration with incremental loading."""
        return SourceConfig(
            name="test_api_incremental",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(base_url="https://api.example.com"),
            resources=[
                ResourceConfig(
                    name="events",
                    endpoint="/events",
                    incremental=IncrementalConfig(
                        enabled=True,
                        cursor_field="updated_at",
                        initial_value="2024-01-01",
                    ),
                    write_disposition=WriteDisposition.MERGE,
                    primary_key=["id"],
                )
            ],
        )

    def test_build_rest_api_config_basic(self, basic_config: SourceConfig) -> None:
        """Test building basic REST API configuration."""
        source = RestApiSource(basic_config, {})
        resource_config = basic_config.resources[0]

        config = source._build_rest_api_config(resource_config)  # type: ignore[attr-defined]

        assert config["client"]["base_url"] == "https://api.example.com"
        assert config["resources"][0]["name"] == "users"
        assert config["resources"][0]["endpoint"]["path"] == "/users"
        assert config["resources"][0]["endpoint"]["method"] == "GET"

    def test_build_auth_config_bearer(self, auth_bearer_config: SourceConfig) -> None:
        """Test building bearer authentication configuration."""
        source = RestApiSource(auth_bearer_config, {})

        auth_config = source._build_auth_config()  # type: ignore[attr-defined]

        assert auth_config is not None
        assert auth_config["type"] == "bearer"
        assert auth_config["token"] == "API_TOKEN"

    def test_build_auth_config_api_key(self) -> None:
        """Test building API key authentication configuration."""
        config = SourceConfig(
            name="test_api",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(
                base_url="https://api.example.com",
                auth=AuthConfig(
                    type=AuthType.API_KEY,
                    credentials_secret_key="MY_API_KEY",
                ),
            ),
            resources=[],
        )
        source = RestApiSource(config, {})

        auth_config = source._build_auth_config()  # type: ignore[attr-defined]

        assert auth_config is not None
        assert auth_config["type"] == "api_key"
        assert auth_config["api_key"] == "MY_API_KEY"

    def test_build_auth_config_basic(self) -> None:
        """Test building basic authentication configuration."""
        config = SourceConfig(
            name="test_api",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(
                base_url="https://api.example.com",
                auth=AuthConfig(
                    type=AuthType.BASIC,
                    username_secret_key="USERNAME",
                    password_secret_key="PASSWORD",
                ),
            ),
            resources=[],
        )
        source = RestApiSource(config, {})

        auth_config = source._build_auth_config()  # type: ignore[attr-defined]

        assert auth_config is not None
        assert auth_config["type"] == "basic"
        assert auth_config["username"] == "USERNAME"
        assert auth_config["password"] == "PASSWORD"

    def test_build_auth_config_none(self, basic_config: SourceConfig) -> None:
        """Test building auth config when no auth is configured."""
        source = RestApiSource(basic_config, {})

        auth_config = source._build_auth_config()  # type: ignore[attr-defined]

        assert auth_config is None

    def test_build_rest_api_config_with_incremental(self, incremental_config: SourceConfig) -> None:
        """Test building REST API configuration with incremental loading."""
        source = RestApiSource(incremental_config, {})
        resource_config = incremental_config.resources[0]

        config = source._build_rest_api_config(resource_config)  # type: ignore[attr-defined]

        assert "incremental" in config["resources"][0]["endpoint"]
        assert config["resources"][0]["endpoint"]["incremental"]["cursor_path"] == "updated_at"
        assert config["resources"][0]["endpoint"]["incremental"]["initial_value"] == "2024-01-01"

    def test_resolve_params_with_placeholders(self, basic_config: SourceConfig) -> None:
        """Test resolving parameters with placeholders."""
        params = {"channel_id": "123", "user_id": "456"}
        source = RestApiSource(basic_config, params)

        input_params = {
            "channelId": "{channel_id}",
            "userId": "{user_id}",
            "fixed": "value",
        }

        resolved = source._resolve_params(input_params)  # type: ignore[attr-defined]

        assert resolved["channelId"] == "123"
        assert resolved["userId"] == "456"
        assert resolved["fixed"] == "value"

    def test_resolve_params_no_placeholders(self, basic_config: SourceConfig) -> None:
        """Test resolving parameters without placeholders."""
        source = RestApiSource(basic_config, {})

        input_params: dict[str, str | int | bool] = {
            "key1": "value1",
            "key2": 123,
            "key3": True,
        }

        resolved = source._resolve_params(input_params)  # type: ignore[attr-defined]

        assert resolved == input_params

    @patch("ingestion.sources.rest_api.rest_api_resources")
    def test_create_resources_basic(
        self, mock_rest_api_resources: MagicMock, basic_config: SourceConfig
    ) -> None:
        """Test creating resources with basic configuration."""
        mock_resource = MagicMock()
        mock_rest_api_resources.return_value = [mock_resource]

        source = RestApiSource(basic_config, {})
        resources = list(source.create_resources(["users"]))

        assert len(resources) == 1
        mock_rest_api_resources.assert_called_once()

    @patch("ingestion.sources.rest_api.rest_api_resources")
    def test_create_resources_with_write_disposition(
        self, mock_rest_api_resources: MagicMock, incremental_config: SourceConfig
    ) -> None:
        """Test creating resources with write disposition."""
        mock_resource = MagicMock()
        mock_resource.apply_hints.return_value = mock_resource
        mock_rest_api_resources.return_value = [mock_resource]

        source = RestApiSource(incremental_config, {})
        resources = list(source.create_resources(["events"]))

        assert len(resources) == 1
        # Check that apply_hints was called for write_disposition
        calls = mock_resource.apply_hints.call_args_list
        assert any("write_disposition" in str(call) for call in calls)

    @patch("ingestion.sources.rest_api.rest_api_resources")
    def test_create_resources_with_primary_key(
        self, mock_rest_api_resources: MagicMock, incremental_config: SourceConfig
    ) -> None:
        """Test creating resources with primary key."""
        mock_resource = MagicMock()
        mock_resource.apply_hints.return_value = mock_resource
        mock_rest_api_resources.return_value = [mock_resource]

        source = RestApiSource(incremental_config, {})
        resources = list(source.create_resources(["events"]))

        assert len(resources) == 1
        # Check that apply_hints was called for primary_key
        calls = mock_resource.apply_hints.call_args_list
        assert any("primary_key" in str(call) for call in calls)

    def test_get_resource_config_from_base_class(self, basic_config: SourceConfig) -> None:
        """Test that get_resource_config is inherited from BaseSource."""
        source = RestApiSource(basic_config, {})

        resource_config = source.get_resource_config("users")
        assert resource_config.name == "users"

        with pytest.raises(ValueError, match="Resource 'nonexistent' not found"):
            source.get_resource_config("nonexistent")

    @patch("ingestion.sources.rest_api.rest_api_resources")
    def test_create_resources_without_primary_key(self, mock_rest_api_resources: MagicMock) -> None:
        """Test creating resources without primary key (empty list skips branch 48)."""
        config = SourceConfig(
            name="test_api",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(base_url="https://api.example.com"),
            resources=[
                ResourceConfig(
                    name="items",
                    endpoint="/items",
                    # primary_key defaults to empty list []
                )
            ],
        )

        mock_resource = MagicMock()
        mock_resource.apply_hints.return_value = mock_resource
        mock_rest_api_resources.return_value = [mock_resource]

        source = RestApiSource(config, {})
        resources = list(source.create_resources(["items"]))

        assert len(resources) == 1
        # Should only call apply_hints for write_disposition (default APPEND), not primary_key
        mock_resource.apply_hints.assert_called_once_with(write_disposition="append")

    def test_build_auth_config_bearer_incomplete(self) -> None:
        """Test building bearer auth config without credentials (returns auth but incomplete)."""
        config = SourceConfig(
            name="test_api",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(
                base_url="https://api.example.com",
                auth=AuthConfig(
                    type=AuthType.BEARER,
                    # No credentials_secret_key
                ),
            ),
            resources=[],
        )
        source = RestApiSource(config, {})

        auth_config = source._build_auth_config()  # type: ignore[attr-defined]

        # Should still return auth config, just without token
        assert auth_config is not None
        assert auth_config["type"] == "bearer"
        assert "token" not in auth_config

    def test_build_auth_config_basic_incomplete(self) -> None:
        """Test building basic auth without username/password (branch 116->121, 117->121)."""
        config = SourceConfig(
            name="test_api",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(
                base_url="https://api.example.com",
                auth=AuthConfig(
                    type=AuthType.BASIC,
                    # No username_secret_key or password_secret_key
                ),
            ),
            resources=[],
        )
        source = RestApiSource(config, {})

        auth_config = source._build_auth_config()  # type: ignore[attr-defined]

        # Should return auth config but without username/password
        assert auth_config is not None
        assert auth_config["type"] == "basic"
        assert "username" not in auth_config
        assert "password" not in auth_config

    def test_build_rest_api_config_with_auth_integrated(
        self, auth_bearer_config: SourceConfig
    ) -> None:
        """Test that auth is integrated into REST API config (lines 81-83)."""
        source = RestApiSource(auth_bearer_config, {})
        resource_config = auth_bearer_config.resources[0]

        config = source._build_rest_api_config(resource_config)  # type: ignore[attr-defined]

        # Auth should be added to client config
        assert "auth" in config["client"]
        assert config["client"]["auth"]["type"] == "bearer"

    def test_build_rest_api_config_no_auth_in_client(self, basic_config: SourceConfig) -> None:
        """Test that auth is not added to client config when no auth configured (branch 82->86)."""
        source = RestApiSource(basic_config, {})
        resource_config = basic_config.resources[0]

        config = source._build_rest_api_config(resource_config)  # type: ignore[attr-defined]

        # Auth should NOT be in client config
        assert "auth" not in config["client"]
