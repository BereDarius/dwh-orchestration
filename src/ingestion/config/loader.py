"""YAML configuration loader."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from ingestion.config.environment import get_environment_config_path
from ingestion.config.models import (
    DestinationConfig,
    Environment,
    PipelineConfig,
    SecretsConfig,
    SourceConfig,
)
from ingestion.config.secrets_resolver import SecretsResolver


class ConfigLoader:
    """Loads and parses YAML configuration files."""

    def __init__(self, environment: Environment | str | None = None) -> None:
        """
        Initialize configuration loader.

        Args:
            environment: Environment to load configs for (defaults to current environment)
        """
        if environment is None:
            from ingestion.config.environment import get_environment

            self.environment = get_environment()
        elif isinstance(environment, Environment):
            self.environment = environment
        else:
            self.environment = Environment(environment)

        self.config_path = get_environment_config_path(self.environment)
        self.secrets_resolver: SecretsResolver | None = None

        # Load secrets config if it exists
        secrets_path = self.config_path / "secrets_mapping.yaml"
        if secrets_path.exists():
            secrets_config = self.load_secrets_config()
            self.secrets_resolver = SecretsResolver(secrets_config)

    @staticmethod
    def _load_yaml(file_path: Path) -> dict[str, Any]:
        """
        Load YAML file.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML content

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path) as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error parsing YAML file {file_path}: {e}") from e

    def load_source_config(self, filename: str) -> SourceConfig:
        """
        Load source configuration.

        Args:
            filename: Name of the source config file (with or without sources/ prefix)

        Returns:
            SourceConfig: Validated source configuration

        Raises:
            ValidationError: If configuration is invalid
        """
        # Remove sources/ prefix if present (loader adds it)
        if filename.startswith("sources/"):
            filename = filename[8:]  # Remove "sources/" prefix

        file_path = self.config_path / "sources" / filename
        data = self._load_yaml(file_path)

        # Extract the source configuration
        source_data = data.get("source", {})

        # Resolve secrets if resolver is available
        if self.secrets_resolver:
            source_data = self.secrets_resolver.resolve_dict(source_data)

        try:
            return SourceConfig(**source_data)
        except ValidationError as e:
            raise ValueError(f"Invalid source configuration in {filename}: {e}") from e

    def load_destination_config(self, filename: str) -> DestinationConfig:
        """
        Load destination configuration.

        Args:
            filename: Name of the destination config file (with or without destinations/ prefix)

        Returns:
            DestinationConfig: Validated destination configuration

        Raises:
            ValidationError: If configuration is invalid
        """
        # Remove destinations/ prefix if present (loader adds it)
        if filename.startswith("destinations/"):
            filename = filename[13:]  # Remove "destinations/" prefix

        file_path = self.config_path / "destinations" / filename
        data = self._load_yaml(file_path)

        # Extract the destination configuration
        dest_data = data.get("destination", {})

        # Resolve secrets if resolver is available
        if self.secrets_resolver:
            dest_data = self.secrets_resolver.resolve_dict(dest_data)

        try:
            return DestinationConfig(**dest_data)
        except ValidationError as e:
            raise ValueError(f"Invalid destination configuration in {filename}: {e}") from e

    def load_pipeline_config(self, filename: str) -> PipelineConfig:
        """
        Load pipeline configuration.

        Args:
            filename: Name of the pipeline config file

        Returns:
            PipelineConfig: Validated pipeline configuration

        Raises:
            ValidationError: If configuration is invalid
        """
        file_path = self.config_path / "pipelines" / filename
        data = self._load_yaml(file_path)

        # Extract the pipeline configuration
        pipeline_data = data.get("pipeline", {})

        # Resolve secrets if resolver is available
        if self.secrets_resolver:
            pipeline_data = self.secrets_resolver.resolve_dict(pipeline_data)

        try:
            return PipelineConfig(**pipeline_data)
        except ValidationError as e:
            raise ValueError(f"Invalid pipeline configuration in {filename}: {e}") from e

    def load_secrets_config(self) -> SecretsConfig:
        """
        Load secrets mapping configuration.

        Returns:
            SecretsConfig: Validated secrets configuration

        Raises:
            ValidationError: If configuration is invalid
        """
        file_path = self.config_path / "secrets_mapping.yaml"
        data = self._load_yaml(file_path)

        try:
            return SecretsConfig(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid secrets configuration: {e}") from e

    def load_all_pipelines(self) -> dict[str, PipelineConfig]:
        """
        Load all pipeline configurations for the current environment.

        Returns:
            Dict mapping pipeline names to their configurations
        """
        pipelines_path = self.config_path / "pipelines"

        if not pipelines_path.exists():
            return {}

        pipelines: dict[str, PipelineConfig] = {}
        for config_file in pipelines_path.glob("*.yaml"):
            pipeline_config = self.load_pipeline_config(config_file.name)
            pipelines[pipeline_config.name] = pipeline_config

        return pipelines

    def load_all_sources(self) -> dict[str, SourceConfig]:
        """
        Load all source configurations for the current environment.

        Returns:
            Dict mapping source names to their configurations
        """
        sources_path = self.config_path / "sources"

        if not sources_path.exists():
            return {}

        sources: dict[str, SourceConfig] = {}
        for config_file in sources_path.glob("*.yaml"):
            try:
                source_config = self.load_source_config(config_file.name)
                sources[source_config.name] = source_config
            except Exception as e:
                # Log error but continue loading other sources
                print(f"Warning: Failed to load source {config_file.name}: {e}")

        return sources

    def load_all_destinations(self) -> dict[str, DestinationConfig]:
        """
        Load all destination configurations for the current environment.

        Returns:
            Dict mapping destination names to their configurations
        """
        destinations_path = self.config_path / "destinations"

        if not destinations_path.exists():
            return {}

        destinations: dict[str, DestinationConfig] = {}
        for config_file in destinations_path.glob("*.yaml"):
            try:
                dest_config = self.load_destination_config(config_file.name)
                destinations[dest_config.name] = dest_config
            except Exception as e:
                # Log error but continue loading other destinations
                print(f"Warning: Failed to load destination {config_file.name}: {e}")

        return destinations

    def discover_all_configs(self) -> dict[str, dict[str, Any]]:
        """
        Discover and load all configurations for the current environment.

        Returns:
            Dict containing all sources, destinations, and pipelines
        """
        return {
            "sources": self.load_all_sources(),
            "destinations": self.load_all_destinations(),
            "pipelines": self.load_all_pipelines(),
        }

    def get_pipeline_files(self) -> list[str]:
        """
        Get list of all pipeline configuration filenames.

        Returns:
            List of pipeline config filenames
        """
        pipelines_path = self.config_path / "pipelines"

        if not pipelines_path.exists():
            return []

        return [f.name for f in pipelines_path.glob("*.yaml")]

    def get_source_files(self) -> list[str]:
        """
        Get list of all source configuration filenames.

        Returns:
            List of source config filenames
        """
        sources_path = self.config_path / "sources"

        if not sources_path.exists():
            return []

        return [f.name for f in sources_path.glob("*.yaml")]

    def get_destination_files(self) -> list[str]:
        """
        Get list of all destination configuration filenames.

        Returns:
            List of destination config filenames
        """
        destinations_path = self.config_path / "destinations"

        if not destinations_path.exists():
            return []

        return [f.name for f in destinations_path.glob("*.yaml")]
