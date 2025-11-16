"""Source factory for creating source instances."""

from typing import Any, Dict, Iterator, List

from dlt.extract.resource import DltResource

from ingestion.config.models import SourceConfig, SourceType
from ingestion.sources.base import BaseSource
from ingestion.sources.rest_api import RestApiSource


class SourceFactory:
    """Factory for creating data source instances."""

    def __init__(self) -> None:
        """Initialize source factory."""
        self._source_map = {
            SourceType.REST_API: RestApiSource,
        }

    def create_source(
        self,
        config: SourceConfig,
        params: Dict[str, Any],
    ) -> BaseSource:
        """
        Create a source instance from configuration.

        Args:
            config: Source configuration
            params: Runtime parameters

        Returns:
            Source instance

        Raises:
            ValueError: If source type is not supported
        """
        source_class = self._source_map.get(config.type)

        if source_class is None:
            raise ValueError(
                f"Unsupported source type: {config.type}. "
                f"Supported types: {list(self._source_map.keys())}"
            )

        return source_class(config, params)

    def create_resources(
        self,
        config: SourceConfig,
        resource_names: List[str],
        params: Dict[str, Any],
    ) -> Iterator[DltResource]:
        """
        Create DLT resources from source configuration.

        Args:
            config: Source configuration
            resource_names: Names of resources to create
            params: Runtime parameters

        Yields:
            DLT resources
        """
        source = self.create_source(config, params)
        yield from source.create_resources(resource_names)
