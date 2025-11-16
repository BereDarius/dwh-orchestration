"""Unit tests for SourceFactory."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ingestion.config.models import (
    ConnectionConfig,
    Environment,
    ResourceConfig,
    SourceConfig,
    SourceType,
)
from ingestion.sources.factory import SourceFactory
from ingestion.sources.rest_api import RestApiSource


class TestSourceFactory:
    """Tests for SourceFactory class."""

    @pytest.fixture
    def factory(self) -> SourceFactory:
        """Create a SourceFactory instance."""
        return SourceFactory()

    @pytest.fixture
    def rest_api_config(self) -> SourceConfig:
        """Create a REST API source configuration."""
        return SourceConfig(
            name="test_rest_api",
            environment=Environment.DEV,
            type=SourceType.REST_API,
            connection=ConnectionConfig(base_url="https://api.example.com"),
            resources=[
                ResourceConfig(name="users", endpoint="/users"),
            ],
        )

    def test_init(self, factory: SourceFactory) -> None:
        """Test SourceFactory initialization."""
        assert hasattr(factory, "_source_map")
        assert SourceType.REST_API in factory._source_map  # type: ignore[attr-defined]
        assert factory._source_map[SourceType.REST_API] == RestApiSource  # type: ignore[attr-defined]

    def test_create_source_rest_api(
        self, factory: SourceFactory, rest_api_config: SourceConfig
    ) -> None:
        """Test creating a REST API source."""
        params = {"channel_id": "123"}
        source = factory.create_source(rest_api_config, params)

        assert isinstance(source, RestApiSource)
        assert source.config == rest_api_config
        assert source.params == params

    def test_create_source_unsupported_type(self, factory: SourceFactory) -> None:
        """Test creating a source with unsupported type."""
        # Use a valid SourceType but one not in the factory's map
        config = SourceConfig(
            name="test_source",
            environment=Environment.DEV,
            type=SourceType.DATABASE,  # Not in factory map
            connection=ConnectionConfig(base_url="https://api.example.com"),
            resources=[],
        )

        with pytest.raises(ValueError, match="Unsupported source type"):
            factory.create_source(config, {})

    @patch.object(RestApiSource, "create_resources")
    def test_create_resources(
        self,
        mock_create_resources: MagicMock,
        factory: SourceFactory,
        rest_api_config: SourceConfig,
    ) -> None:
        """Test creating resources from source configuration."""
        # Mock the create_resources method to return a mock resource
        mock_resource = MagicMock()
        mock_create_resources.return_value = iter([mock_resource])

        resource_names = ["users"]
        params: dict[str, Any] = {"channel_id": "123"}

        resources = list(factory.create_resources(rest_api_config, resource_names, params))

        assert len(resources) == 1
        assert resources[0] == mock_resource
        mock_create_resources.assert_called_once_with(resource_names)
