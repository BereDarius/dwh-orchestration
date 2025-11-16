"""Base source interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List

from dlt.extract.resource import DltResource

from ingestion.config.models import ResourceConfig, SourceConfig


class BaseSource(ABC):
    """Base class for all data sources."""

    def __init__(self, config: SourceConfig, params: Dict[str, Any]) -> None:
        """
        Initialize source.

        Args:
            config: Source configuration
            params: Runtime parameters
        """
        self.config = config
        self.params = params

    @abstractmethod
    def create_resources(
        self,
        resource_names: List[str],
    ) -> Iterator[DltResource]:
        """
        Create DLT resources for this source.

        Args:
            resource_names: Names of resources to create

        Yields:
            DLT resources
        """
        pass

    def get_resource_config(self, resource_name: str) -> ResourceConfig:
        """
        Get configuration for a specific resource.

        Args:
            resource_name: Name of the resource

        Returns:
            Resource configuration

        Raises:
            ValueError: If resource not found
        """
        for resource in self.config.resources:
            if resource.name == resource_name:
                return resource

        raise ValueError(f"Resource '{resource_name}' not found in source '{self.config.name}'")
