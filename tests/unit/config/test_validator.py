"""Unit tests for configuration validator."""

import pytest

from ingestion.config.models import (
    AuthConfig,
    ConnectionConfig,
    DestinationConfig,
    DestinationConnectionConfig,
    DestinationSettings,
    DestinationType,
    Environment,
    ExecutionConfig,
    IncrementalConfig,
    PipelineConfig,
    PipelineDestinationRef,
    PipelineSourceRef,
    ResourceConfig,
    ScheduleConfig,
    SourceConfig,
    WriteDisposition,
)
from ingestion.config.validator import ConfigValidator


@pytest.fixture
def valid_source_config() -> SourceConfig:
    """Valid source configuration."""
    return SourceConfig(
        name="test_source",
        environment=Environment.DEV,
        type="rest_api",  # type: ignore[arg-type]
        connection=ConnectionConfig(
            base_url="https://api.example.com",
            auth=AuthConfig(type="bearer", token_secret_key="API_TOKEN"),  # type: ignore[arg-type]
        ),
        resources=[
            ResourceConfig(
                name="users",
                endpoint="/users",
                write_disposition=WriteDisposition.APPEND,
            )
        ],
    )


@pytest.fixture
def valid_destination_config() -> DestinationConfig:
    """Valid destination configuration."""
    return DestinationConfig(
        name="test_databricks",
        environment=Environment.DEV,
        type=DestinationType.DATABRICKS,
        connection=DestinationConnectionConfig(
            server_hostname_secret_key="DATABRICKS_HOST",
            http_path_secret_key="DATABRICKS_PATH",
            access_token_secret_key="DATABRICKS_TOKEN",
            catalog="main",
            db_schema="default",
        ),
        settings=DestinationSettings(
            vacuum_after_write=True,
            vacuum_retention_hours=168,
        ),
    )


@pytest.fixture
def valid_pipeline_config() -> PipelineConfig:
    """Valid pipeline configuration."""
    return PipelineConfig(
        name="test_pipeline",
        environment=Environment.DEV,
        source=PipelineSourceRef(config_file="source.yaml", resources=["users"]),
        destination=PipelineDestinationRef(config_file="destination.yaml", dataset_name="raw"),
        schedule=ScheduleConfig(enabled=False, cron="0 0 * * *"),
        execution=ExecutionConfig(timeout=300, parallelism=4),
        sla_hours=24,
    )


class TestValidateSourceConfig:
    """Tests for validate_source_config."""

    def test_valid_source_config(self, valid_source_config: SourceConfig) -> None:
        """Test validation of a valid source config."""
        errors = ConfigValidator.validate_source_config(valid_source_config)
        assert errors == []

    def test_source_no_resources(self) -> None:
        """Test validation fails when no resources defined."""
        config = SourceConfig(
            name="test_source",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(base_url="https://api.example.com"),
            resources=[],
        )
        errors = ConfigValidator.validate_source_config(config)
        assert len(errors) == 1
        assert "must have at least one resource" in errors[0]

    def test_incremental_without_cursor_field(self) -> None:
        """Test validation fails when incremental enabled but no cursor_field."""
        config = SourceConfig(
            name="test_source",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(base_url="https://api.example.com"),
            resources=[
                ResourceConfig(
                    name="events",
                    endpoint="/events",
                    write_disposition=WriteDisposition.APPEND,
                    incremental=IncrementalConfig(
                        enabled=True,
                        cursor_field="",  # Empty cursor field
                        initial_value="2024-01-01",
                    ),
                )
            ],
        )
        errors = ConfigValidator.validate_source_config(config)
        assert len(errors) == 1
        assert "incremental enabled but cursor_field not set" in errors[0]
        assert "events" in errors[0]

    def test_merge_without_primary_key(self) -> None:
        """Test validation fails when merge disposition without primary key."""
        config = SourceConfig(
            name="test_source",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(base_url="https://api.example.com"),
            resources=[
                ResourceConfig(
                    name="users",
                    endpoint="/users",
                    write_disposition=WriteDisposition.MERGE,
                    # No primary_key defined
                )
            ],
        )
        errors = ConfigValidator.validate_source_config(config)
        assert len(errors) == 1
        assert "write_disposition is 'merge'" in errors[0]
        assert "no primary_key defined" in errors[0]
        assert "users" in errors[0]

    def test_resource_without_incremental(self) -> None:
        """Test no error when resource has no incremental config (None)."""
        config = SourceConfig(
            name="test_source",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(base_url="https://api.example.com"),
            resources=[
                ResourceConfig(
                    name="events",
                    endpoint="/events",
                    write_disposition=WriteDisposition.APPEND,
                    # incremental is None by default
                )
            ],
        )
        errors = ConfigValidator.validate_source_config(config)
        assert errors == []

    def test_incremental_with_cursor_field(self) -> None:
        """Test no error when incremental enabled with valid cursor_field."""
        config = SourceConfig(
            name="test_source",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(base_url="https://api.example.com"),
            resources=[
                ResourceConfig(
                    name="events",
                    endpoint="/events",
                    write_disposition=WriteDisposition.APPEND,
                    incremental=IncrementalConfig(
                        enabled=True,
                        cursor_field="updated_at",  # Valid cursor field
                        initial_value="2024-01-01",
                    ),
                )
            ],
        )
        errors = ConfigValidator.validate_source_config(config)
        assert errors == []


class TestValidateDestinationConfig:
    """Tests for validate_destination_config."""

    def test_valid_databricks_config(self, valid_destination_config: DestinationConfig) -> None:
        """Test validation passes for valid Databricks config."""
        errors = ConfigValidator.validate_destination_config(valid_destination_config)
        assert errors == []

    def test_databricks_missing_server_hostname(self) -> None:
        """Test validation fails when Databricks missing server_hostname."""
        config = DestinationConfig(
            name="test_databricks",
            environment=Environment.DEV,
            type=DestinationType.DATABRICKS,
            connection=DestinationConnectionConfig(
                server_hostname_secret_key="",  # Missing
                http_path_secret_key="DATABRICKS_PATH",
                access_token_secret_key="DATABRICKS_TOKEN",
            ),
        )
        errors = ConfigValidator.validate_destination_config(config)
        assert len(errors) == 1
        assert "server_hostname_secret_key" in errors[0]

    def test_databricks_missing_http_path(self) -> None:
        """Test validation fails when Databricks missing http_path."""
        config = DestinationConfig(
            name="test_databricks",
            environment=Environment.DEV,
            type=DestinationType.DATABRICKS,
            connection=DestinationConnectionConfig(
                server_hostname_secret_key="DATABRICKS_HOST",
                http_path_secret_key="",  # Missing
                access_token_secret_key="DATABRICKS_TOKEN",
            ),
        )
        errors = ConfigValidator.validate_destination_config(config)
        assert len(errors) == 1
        assert "http_path_secret_key" in errors[0]

    def test_databricks_missing_access_token(self) -> None:
        """Test validation fails when Databricks missing access_token."""
        config = DestinationConfig(
            name="test_databricks",
            environment=Environment.DEV,
            type=DestinationType.DATABRICKS,
            connection=DestinationConnectionConfig(
                server_hostname_secret_key="DATABRICKS_HOST",
                http_path_secret_key="DATABRICKS_PATH",
                access_token_secret_key="",  # Missing
            ),
        )
        errors = ConfigValidator.validate_destination_config(config)
        assert len(errors) == 1
        assert "access_token_secret_key" in errors[0]

    def test_vacuum_retention_too_low(self) -> None:
        """Test validation fails when vacuum retention below minimum."""
        config = DestinationConfig(
            name="test_databricks",
            environment=Environment.DEV,
            type=DestinationType.DATABRICKS,
            connection=DestinationConnectionConfig(
                server_hostname_secret_key="DATABRICKS_HOST",
                http_path_secret_key="DATABRICKS_PATH",
                access_token_secret_key="DATABRICKS_TOKEN",
            ),
            settings=DestinationSettings(
                vacuum_after_write=True,
                vacuum_retention_hours=24,  # Too low
            ),
        )
        errors = ConfigValidator.validate_destination_config(config)
        assert len(errors) == 1
        assert "vacuum_retention_hours must be at least 168" in errors[0]

    def test_non_databricks_destination(self) -> None:
        """Test validation for non-Databricks destination type."""
        # Test with Snowflake destination type - should skip Databricks-specific validation
        config = DestinationConfig(
            name="test_snowflake",
            environment=Environment.DEV,
            type=DestinationType.SNOWFLAKE,
            connection=DestinationConnectionConfig(
                # Non-Databricks destinations don't require Databricks-specific fields
                catalog="test_catalog",
                db_schema="test_schema",
            ),
            settings=DestinationSettings(
                vacuum_after_write=False,
                vacuum_retention_hours=200,
            ),
        )
        errors = ConfigValidator.validate_destination_config(config)
        # Should pass validation since it's not databricks
        assert errors == []


class TestValidatePipelineConfig:
    """Tests for validate_pipeline_config."""

    def test_valid_pipeline_config(self, valid_pipeline_config: PipelineConfig) -> None:
        """Test validation passes for valid pipeline config."""
        errors = ConfigValidator.validate_pipeline_config(valid_pipeline_config)
        assert errors == []

    def test_invalid_cron_expression(self) -> None:
        """Test validation fails for invalid cron expression."""
        config = PipelineConfig(
            name="test_pipeline",
            environment=Environment.DEV,
            source=PipelineSourceRef(config_file="source.yaml", resources=["users"]),
            destination=PipelineDestinationRef(config_file="dest.yaml", dataset_name="raw"),
            schedule=ScheduleConfig(enabled=True, cron="0 0 *"),  # Only 3 parts
            execution=ExecutionConfig(),
            sla_hours=24,
        )
        errors = ConfigValidator.validate_pipeline_config(config)
        assert len(errors) == 1
        assert "Invalid cron expression" in errors[0]
        assert "Must have 5 parts" in errors[0]

    def test_valid_cron_expression(self) -> None:
        """Test validation passes for valid cron expression."""
        config = PipelineConfig(
            name="test_pipeline",
            environment=Environment.DEV,
            source=PipelineSourceRef(config_file="source.yaml", resources=["users"]),
            destination=PipelineDestinationRef(config_file="dest.yaml", dataset_name="raw"),
            schedule=ScheduleConfig(enabled=True, cron="0 0 * * *"),  # Valid 5 parts
            execution=ExecutionConfig(),
            sla_hours=24,
        )
        errors = ConfigValidator.validate_pipeline_config(config)
        # Should have no cron errors, only validates cron format
        assert all("Invalid cron expression" not in error for error in errors)

    def test_sla_hours_too_low(self) -> None:
        """Test validation fails when SLA hours is too low."""
        config = PipelineConfig(
            name="test_pipeline",
            environment=Environment.DEV,
            source=PipelineSourceRef(config_file="source.yaml", resources=["users"]),
            destination=PipelineDestinationRef(config_file="destination.yaml", dataset_name="raw"),
            schedule=ScheduleConfig(enabled=False, cron="0 0 * * *"),
            execution=ExecutionConfig(timeout=300, parallelism=4),
            sla_hours=0,  # SLA < 1
        )
        errors = ConfigValidator.validate_pipeline_config(config)
        assert len(errors) == 1
        assert "SLA hours must be at least 1" in errors[0]

    def test_resource_not_in_source(self, valid_source_config: SourceConfig) -> None:
        """Test validation fails when pipeline references non-existent resource."""
        pipeline_config = PipelineConfig(
            name="test_pipeline",
            environment=Environment.DEV,
            source=PipelineSourceRef(
                config_file="source.yaml",
                resources=["users", "events"],  # events doesn't exist
            ),
            destination=PipelineDestinationRef(config_file="dest.yaml", dataset_name="raw"),
            schedule=ScheduleConfig(enabled=False, cron="0 0 * * *"),
            execution=ExecutionConfig(),
            sla_hours=24,
        )
        errors = ConfigValidator.validate_pipeline_config(pipeline_config, valid_source_config)
        assert len(errors) == 1
        assert "Resource 'events' requested" in errors[0]
        assert "not defined in source" in errors[0]

    def test_environment_mismatch_source(self) -> None:
        """Test validation fails when pipeline and source environments differ."""
        source_config = SourceConfig(
            name="test_source",
            environment=Environment.PROD,  # Different environment
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(base_url="https://api.example.com"),
            resources=[ResourceConfig(name="users", endpoint="/users")],
        )
        pipeline_config = PipelineConfig(
            name="test_pipeline",
            environment=Environment.DEV,
            source=PipelineSourceRef(config_file="source.yaml", resources=["users"]),
            destination=PipelineDestinationRef(config_file="dest.yaml", dataset_name="raw"),
            schedule=ScheduleConfig(enabled=False, cron="0 0 * * *"),
            execution=ExecutionConfig(),
            sla_hours=24,
        )
        errors = ConfigValidator.validate_pipeline_config(pipeline_config, source_config)
        assert len(errors) == 1
        assert "Environment mismatch" in errors[0]
        assert "pipeline is dev" in errors[0]
        assert "source is prod" in errors[0]

    def test_environment_mismatch_destination(self) -> None:
        """Test validation fails when pipeline and destination environments differ."""
        destination_config = DestinationConfig(
            name="test_dest",
            environment=Environment.STAGE,  # Different environment
            type=DestinationType.DATABRICKS,
            connection=DestinationConnectionConfig(
                server_hostname_secret_key="DATABRICKS_HOST",
                http_path_secret_key="DATABRICKS_PATH",
                access_token_secret_key="DATABRICKS_TOKEN",
            ),
        )
        pipeline_config = PipelineConfig(
            name="test_pipeline",
            environment=Environment.DEV,
            source=PipelineSourceRef(config_file="source.yaml", resources=["users"]),
            destination=PipelineDestinationRef(config_file="dest.yaml", dataset_name="raw"),
            schedule=ScheduleConfig(enabled=False, cron="0 0 * * *"),
            execution=ExecutionConfig(),
            sla_hours=24,
        )
        errors = ConfigValidator.validate_pipeline_config(
            pipeline_config, destination_config=destination_config
        )
        assert len(errors) == 1
        assert "Environment mismatch" in errors[0]
        assert "pipeline is dev" in errors[0]
        assert "destination is stage" in errors[0]

    def test_pipeline_without_source_config(self, valid_pipeline_config: PipelineConfig) -> None:
        """Test validation passes when no source config provided."""
        # When source_config is None, should still validate schedule and SLA
        errors = ConfigValidator.validate_pipeline_config(
            valid_pipeline_config, source_config=None, destination_config=None
        )
        # No errors expected for valid pipeline when source_config is not checked
        assert errors == []

    def test_pipeline_with_valid_source_config(self, valid_source_config: SourceConfig) -> None:
        """Test validation passes when source config provided with matching resources and environment."""
        # Pipeline requesting resources that exist in source with matching environment
        pipeline_config = PipelineConfig(
            name="test_pipeline",
            environment=Environment.DEV,
            source=PipelineSourceRef(
                config_file="source.yaml",
                resources=["users"],  # This resource exists in valid_source_config
            ),
            destination=PipelineDestinationRef(config_file="dest.yaml", dataset_name="raw"),
            schedule=ScheduleConfig(enabled=False, cron="0 0 * * *"),
            execution=ExecutionConfig(),
            sla_hours=24,
        )
        errors = ConfigValidator.validate_pipeline_config(pipeline_config, valid_source_config)
        # No errors expected when all resources exist and environment matches
        assert errors == []


class TestValidateAll:
    """Tests for validate_all."""

    def test_validate_all_success(
        self,
        valid_source_config: SourceConfig,
        valid_destination_config: DestinationConfig,
        valid_pipeline_config: PipelineConfig,
    ) -> None:
        """Test validate_all returns no errors for valid configs."""
        results = ConfigValidator.validate_all(
            valid_source_config, valid_destination_config, valid_pipeline_config
        )
        assert "source" in results
        assert "destination" in results
        assert "pipeline" in results
        assert results["source"] == []
        assert results["destination"] == []
        assert results["pipeline"] == []

    def test_validate_all_with_errors(self) -> None:
        """Test validate_all captures all errors across configs."""
        source_config = SourceConfig(
            name="test_source",
            environment=Environment.DEV,
            type="rest_api",  # type: ignore[arg-type]
            connection=ConnectionConfig(base_url="https://api.example.com"),
            resources=[],  # No resources
        )
        destination_config = DestinationConfig(
            name="test_dest",
            environment=Environment.DEV,
            type=DestinationType.DATABRICKS,
            connection=DestinationConnectionConfig(
                server_hostname_secret_key="",  # Missing
                http_path_secret_key="DATABRICKS_PATH",
                access_token_secret_key="DATABRICKS_TOKEN",
            ),
        )
        pipeline_config = PipelineConfig(
            name="test_pipeline",
            environment=Environment.DEV,
            source=PipelineSourceRef(config_file="source.yaml", resources=["users"]),
            destination=PipelineDestinationRef(config_file="dest.yaml", dataset_name="raw"),
            schedule=ScheduleConfig(enabled=True, cron="invalid"),  # Invalid cron
            execution=ExecutionConfig(),
            sla_hours=24,
        )
        results = ConfigValidator.validate_all(source_config, destination_config, pipeline_config)
        assert len(results["source"]) == 1
        assert len(results["destination"]) == 1
        # Pipeline has 2 errors: invalid cron + missing resource
        assert len(results["pipeline"]) == 2


class TestHasErrors:
    """Tests for has_errors helper."""

    def test_has_errors_true(self) -> None:
        """Test has_errors returns True when errors exist."""
        results: dict[str, list[str]] = {
            "source": ["Error 1"],
            "destination": [],
            "pipeline": [],
        }
        assert ConfigValidator.has_errors(results) is True

    def test_has_errors_false(self) -> None:
        """Test has_errors returns False when no errors."""
        results: dict[str, list[str]] = {
            "source": [],
            "destination": [],
            "pipeline": [],
        }
        assert ConfigValidator.has_errors(results) is False

    def test_has_errors_multiple(self) -> None:
        """Test has_errors returns True when multiple error types exist."""
        results: dict[str, list[str]] = {
            "source": ["Error 1", "Error 2"],
            "destination": ["Error 3"],
            "pipeline": [],
        }
        assert ConfigValidator.has_errors(results) is True
