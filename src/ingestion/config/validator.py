"""Configuration validation utilities."""

from ingestion.config.models import DestinationConfig, PipelineConfig, SourceConfig


class ConfigValidator:
    """Validates configuration files and their relationships."""

    @staticmethod
    def validate_source_config(config: SourceConfig) -> list[str]:
        """
        Validate source configuration.

        Args:
            config: Source configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        # Validate that at least one resource is defined
        if not config.resources:
            errors.append("Source must have at least one resource defined")

        # Validate each resource
        for resource in config.resources:
            # Check that incremental config is valid
            if resource.incremental and resource.incremental.enabled:
                if not resource.incremental.cursor_field:
                    errors.append(
                        f"Resource '{resource.name}': incremental enabled but cursor_field not set"
                    )

            # Check that primary key is defined for merge disposition
            if resource.write_disposition.value == "merge" and not resource.primary_key:
                errors.append(
                    f"Resource '{resource.name}': write_disposition is 'merge' "
                    "but no primary_key defined"
                )

        return errors

    @staticmethod
    def validate_destination_config(config: DestinationConfig) -> list[str]:
        """
        Validate destination configuration.

        Args:
            config: Destination configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        # Validate connection settings based on destination type
        if config.type.value == "databricks":
            if not config.connection.server_hostname_secret_key:
                errors.append("Databricks destination requires server_hostname_secret_key")
            if not config.connection.http_path_secret_key:
                errors.append("Databricks destination requires http_path_secret_key")
            if not config.connection.access_token_secret_key:
                errors.append("Databricks destination requires access_token_secret_key")

        # Validate vacuum retention
        if config.settings.vacuum_after_write:
            if config.settings.vacuum_retention_hours < 168:
                errors.append(
                    "vacuum_retention_hours must be at least 168 (7 days) " "to prevent data loss"
                )

        return errors

    @staticmethod
    def validate_pipeline_config(
        config: PipelineConfig,
        source_config: SourceConfig | None = None,
        destination_config: DestinationConfig | None = None,
    ) -> list[str]:
        """
        Validate pipeline configuration.

        Args:
            config: Pipeline configuration to validate
            source_config: Optional source config to validate against
            destination_config: Optional destination config to validate against

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        # Validate schedule
        if config.schedule.enabled:
            # Basic cron validation (should have 5 parts)
            cron_parts = config.schedule.cron.strip().split()
            if len(cron_parts) != 5:
                errors.append(
                    f"Invalid cron expression: '{config.schedule.cron}'. "
                    "Must have 5 parts (minute hour day month day_of_week)"
                )

        # Validate SLA
        if config.sla_hours < 1:
            errors.append("SLA hours must be at least 1")

        # Validate against source config if provided
        if source_config:
            # Check that requested resources exist in source
            available_resources = {r.name for r in source_config.resources}
            for resource_name in config.source.resources:
                if resource_name not in available_resources:
                    errors.append(
                        f"Resource '{resource_name}' requested in pipeline but not "
                        f"defined in source. Available: {available_resources}"
                    )

            # Check environment consistency
            if config.environment != source_config.environment:
                errors.append(
                    f"Environment mismatch: pipeline is {config.environment.value}, "
                    f"source is {source_config.environment.value}"
                )

        # Validate against destination config if provided
        if destination_config:
            # Check environment consistency
            if config.environment != destination_config.environment:
                errors.append(
                    f"Environment mismatch: pipeline is {config.environment.value}, "
                    f"destination is {destination_config.environment.value}"
                )

        return errors

    @staticmethod
    def validate_all(
        source_config: SourceConfig,
        destination_config: DestinationConfig,
        pipeline_config: PipelineConfig,
    ) -> dict[str, list[str]]:
        """
        Validate all configurations together.

        Args:
            source_config: Source configuration
            destination_config: Destination configuration
            pipeline_config: Pipeline configuration

        Returns:
            Dictionary of validation errors by component
        """
        return {
            "source": ConfigValidator.validate_source_config(source_config),
            "destination": ConfigValidator.validate_destination_config(destination_config),
            "pipeline": ConfigValidator.validate_pipeline_config(
                pipeline_config, source_config, destination_config
            ),
        }

    @staticmethod
    def has_errors(validation_results: dict[str, list[str]]) -> bool:
        """
        Check if validation results contain any errors.

        Args:
            validation_results: Results from validate_all()

        Returns:
            True if any errors exist
        """
        return any(len(errors) > 0 for errors in validation_results.values())
