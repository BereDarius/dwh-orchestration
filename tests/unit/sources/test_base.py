"""Unit tests for BaseSource."""

from collections.abc import Iterator

import pytest
from dlt.extract.resource import DltResource

from ingestion.config.models import ConnectionConfig, Environment, ResourceConfig, SourceConfig
from ingestion.sources.base import BaseSource


class TestBaseSource:
    """Tests for BaseSource class."""

    @pytest.fixture
    def source_config(self) -> SourceConfig:
        """Create a sample source configuration."""
        return SourceConfig(
            name="test_source",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(base_url="https://api.example.com"),
            resources=[
                ResourceConfig(name="users", endpoint="/users"),
                ResourceConfig(name="posts", endpoint="/posts"),
            ],
        )

    @pytest.fixture
    def concrete_source(self, source_config: SourceConfig) -> BaseSource:
        """Create a concrete implementation of BaseSource for testing."""

        class ConcreteSource(BaseSource):
            def create_resources(self, resource_names: list[str]) -> Iterator[DltResource]:
                """Mock implementation."""
                yield from []

        return ConcreteSource(source_config, {"param1": "value1"})

    def test_init(self, source_config: SourceConfig) -> None:
        """Test BaseSource initialization."""

        class ConcreteSource(BaseSource):
            def create_resources(self, resource_names: list[str]) -> Iterator[DltResource]:
                yield from []

        params = {"channel_id": "123", "api_version": "v2"}
        source = ConcreteSource(source_config, params)

        assert source.config == source_config
        assert source.params == params

    def test_get_resource_config_found(self, concrete_source: BaseSource) -> None:
        """Test getting configuration for an existing resource."""
        resource_config = concrete_source.get_resource_config("users")

        assert resource_config.name == "users"
        assert resource_config.endpoint == "/users"

    def test_get_resource_config_not_found(self, concrete_source: BaseSource) -> None:
        """Test getting configuration for a non-existent resource."""
        with pytest.raises(ValueError, match="Resource 'nonexistent' not found"):
            concrete_source.get_resource_config("nonexistent")

    def test_create_resources_abstract(self, source_config: SourceConfig) -> None:
        """Test that create_resources is abstract and must be implemented."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseSource(source_config, {})  # type: ignore[abstract]
