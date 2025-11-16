"""Pipeline factory for creating DLT pipelines from configuration."""

from typing import Any, Dict, Iterator, Optional

import dlt
from dlt.common.typing import TDataItem
from dlt.extract.resource import DltResource

from ingestion.config.loader import ConfigLoader
from ingestion.config.models import (
    DestinationConfig,
    Environment,
    PipelineConfig,
    SourceConfig,
)
from ingestion.sources.factory import SourceFactory


class PipelineFactory:
    """Factory for creating DLT pipelines from YAML configuration."""

    def __init__(self, environment: Optional[Environment] = None) -> None:
        """
        Initialize pipeline factory.

        Args:
            environment: Environment to create pipelines for
        """
        self.config_loader = ConfigLoader(environment)
        self.environment = self.config_loader.environment

    def create_pipeline(
        self,
        pipeline_config: PipelineConfig,
        source_config: Optional[SourceConfig] = None,
        destination_config: Optional[DestinationConfig] = None,
    ) -> dlt.Pipeline:
        """
        Create a DLT pipeline from configuration.

        Args:
            pipeline_config: Pipeline configuration
            source_config: Optional source config (will be loaded if not provided)
            destination_config: Optional destination config (will be loaded if not provided)

        Returns:
            Configured DLT pipeline
        """
        # Load source and destination configs if not provided
        if source_config is None:
            source_config = self.config_loader.load_source_config(
                pipeline_config.source.config_file
            )

        if destination_config is None:
            destination_config = self.config_loader.load_destination_config(
                pipeline_config.destination.config_file
            )

        # Create DLT pipeline
        pipeline = dlt.pipeline(
            pipeline_name=pipeline_config.name,
            destination=self._get_destination_name(destination_config),
            dataset_name=pipeline_config.destination.dataset_name,
            progress="log",
        )

        return pipeline

    def create_source(
        self,
        source_config: SourceConfig,
        pipeline_config: PipelineConfig,
    ) -> Iterator[DltResource]:
        """
        Create DLT source from configuration.

        Args:
            source_config: Source configuration
            pipeline_config: Pipeline configuration

        Returns:
            DLT source with configured resources
        """
        # Use source factory to create the source
        source_factory = SourceFactory()

        # Get requested resources
        requested_resources = pipeline_config.source.resources

        # Get runtime parameters
        params = pipeline_config.source.params

        # Create and yield resources
        for resource in source_factory.create_resources(
            source_config,
            requested_resources,
            params,
        ):
            yield resource

    def load_and_create_pipeline(self, pipeline_name: str) -> dlt.Pipeline:
        """
        Load configuration and create pipeline by name.

        Args:
            pipeline_name: Name of the pipeline (filename without .yaml)

        Returns:
            Configured DLT pipeline
        """
        # Load pipeline config
        pipeline_config = self.config_loader.load_pipeline_config(f"{pipeline_name}.yaml")

        # Load source and destination configs
        source_config = self.config_loader.load_source_config(pipeline_config.source.config_file)
        destination_config = self.config_loader.load_destination_config(
            pipeline_config.destination.config_file
        )

        # Create pipeline
        return self.create_pipeline(pipeline_config, source_config, destination_config)

    @staticmethod
    def _get_destination_name(destination_config: DestinationConfig) -> str:
        """
        Get DLT destination name from config.

        Args:
            destination_config: Destination configuration

        Returns:
            DLT destination name
        """
        destination_map = {
            "databricks": "databricks",
            "snowflake": "snowflake",
            "bigquery": "bigquery",
            "postgres": "postgres",
            "duckdb": "duckdb",
        }

        return destination_map.get(
            destination_config.type.value,
            destination_config.type.value,
        )

    def get_destination_credentials(
        self,
        destination_config: DestinationConfig,
    ) -> Dict[str, Any]:
        """
        Get destination credentials from configuration.

        Args:
            destination_config: Destination configuration

        Returns:
            Dictionary of credentials for the destination
        """
        credentials: Dict[str, Any] = {}

        if destination_config.type.value == "databricks":
            # Credentials were already resolved by secrets_resolver
            credentials = {
                "server_hostname": destination_config.connection.server_hostname_secret_key,
                "http_path": destination_config.connection.http_path_secret_key,
                "access_token": destination_config.connection.access_token_secret_key,
                "catalog": destination_config.connection.catalog,
                "schema": destination_config.connection.schema,
            }

        return credentials
