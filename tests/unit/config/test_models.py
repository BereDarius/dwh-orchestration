"""Unit tests for configuration models."""

from typing import Any

import pytest
from pydantic import ValidationError

from ingestion.config.models import (
    AuthConfig,
    ConnectionConfig,
    DestinationConfig,
    DestinationConnectionConfig,
    Environment,
    ExecutionConfig,
    IncrementalConfig,
    MonitoringConfig,
    PipelineConfig,
    PipelineDestinationRef,
    PipelineSourceRef,
    ResourceConfig,
    RetryConfig,
    ScheduleConfig,
    SecretsConfig,
    SourceConfig,
    WriteDisposition,
)


class TestEnvironment:
    """Tests for Environment enum."""

    def test_environment_values(self):
        """Test environment enum values."""
        assert Environment.DEV.value == "dev"
        assert Environment.STAGE.value == "stage"
        assert Environment.PROD.value == "prod"

    def test_environment_from_string(self):
        """Test creating environment from string."""
        assert Environment("dev") == Environment.DEV
        assert Environment("stage") == Environment.STAGE
        assert Environment("prod") == Environment.PROD

    def test_environment_invalid_value(self):
        """Test invalid environment value."""
        with pytest.raises(ValueError):
            Environment("invalid")


class TestAuthConfig:
    """Tests for AuthConfig model."""

    def test_bearer_auth(self):
        """Test bearer token authentication."""
        auth = AuthConfig(type="bearer", credentials_secret_key="API_KEY")  # type: ignore[arg-type]
        assert auth.type == "bearer"
        assert auth.credentials_secret_key == "API_KEY"

    def test_api_key_auth(self):
        """Test API key authentication."""
        auth = AuthConfig(
            type="api_key", credentials_secret_key="API_KEY"  # type: ignore[arg-type]
        )
        assert auth.type == "api_key"
        assert auth.credentials_secret_key == "API_KEY"

    def test_basic_auth(self):
        """Test basic authentication."""
        auth = AuthConfig(
            type="basic",  # type: ignore[arg-type]
            username_secret_key="USERNAME",
            password_secret_key="PASSWORD",
        )
        assert auth.type == "basic"
        assert auth.username_secret_key == "USERNAME"
        assert auth.password_secret_key == "PASSWORD"

    def test_oauth2_auth(self):
        """Test OAuth2 authentication."""
        auth = AuthConfig(type="oauth2", token_secret_key="OAUTH_TOKEN")  # type: ignore[arg-type]
        assert auth.type == "oauth2"
        assert auth.token_secret_key == "OAUTH_TOKEN"


class TestRetryConfig:
    """Tests for RetryConfig model."""

    def test_default_retry_config(self):
        """Test default retry configuration."""
        retry = RetryConfig()
        assert retry.max_attempts == 3
        assert retry.backoff_factor == 2
        assert retry.backoff_max == 60

    def test_custom_retry_config(self):
        """Test custom retry configuration."""
        retry = RetryConfig(max_attempts=5, backoff_factor=3, backoff_max=600)
        assert retry.max_attempts == 5
        assert retry.backoff_factor == 3
        assert retry.backoff_max == 600

    def test_invalid_retry_config(self):
        """Test invalid retry configuration."""
        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=0)  # Must be >= 1


class TestIncrementalConfig:
    """Tests for IncrementalConfig model."""

    def test_enabled_incremental(self):
        """Test enabled incremental configuration."""
        incremental = IncrementalConfig(
            enabled=True, cursor_field="updated_at", initial_value="2024-01-01T00:00:00Z"
        )
        assert incremental.enabled is True
        assert incremental.cursor_field == "updated_at"
        assert incremental.initial_value == "2024-01-01T00:00:00Z"

    def test_disabled_incremental(self):
        """Test disabled incremental configuration."""
        incremental = IncrementalConfig(enabled=False, cursor_field="id", initial_value="0")
        assert incremental.enabled is False
        assert incremental.cursor_field == "id"

    def test_incremental_validation(self):
        """Test incremental configuration validation."""
        # All required fields must be provided
        incremental = IncrementalConfig(
            enabled=True, cursor_field="updated_at", initial_value="2024-01-01"
        )
        assert incremental.enabled is True
        assert incremental.cursor_field == "updated_at"


class TestResourceConfig:
    """Tests for ResourceConfig model."""

    def test_basic_resource(self):
        """Test basic resource configuration."""
        resource = ResourceConfig(name="users", endpoint="/users", method="GET", primary_key=["id"])
        assert resource.name == "users"
        assert resource.endpoint == "/users"
        assert resource.method == "GET"
        assert resource.primary_key == ["id"]
        assert resource.write_disposition == WriteDisposition.APPEND  # default

    def test_resource_with_incremental(self):
        """Test resource with incremental loading."""
        resource = ResourceConfig(
            name="users",
            endpoint="/users",
            method="GET",
            primary_key=["id"],
            incremental=IncrementalConfig(
                enabled=True, cursor_field="updated_at", initial_value="2024-01-01T00:00:00Z"
            ),
            write_disposition="merge",  # type: ignore[arg-type]
        )
        assert resource.incremental.enabled is True  # type: ignore[union-attr]
        assert resource.write_disposition == "merge"

    def test_resource_with_params(self):
        """Test resource with parameters."""
        resource = ResourceConfig(
            name="users",
            endpoint="/users",
            method="GET",
            params={"status": "active", "limit": 100},
            primary_key=["id"],
        )
        assert resource.params == {"status": "active", "limit": 100}


class TestConnectionConfig:
    """Tests for ConnectionConfig model."""

    def test_rest_api_connection(self):
        """Test REST API connection configuration."""
        conn = ConnectionConfig(
            base_url="https://api.test.com",
            auth=AuthConfig(type="bearer", credentials_secret_key="API_KEY"),  # type: ignore[arg-type]
            timeout=30,
            retry=RetryConfig(max_attempts=3),
        )
        assert conn.base_url == "https://api.test.com"
        assert conn.timeout == 30
        assert conn.auth.type == "bearer"  # type: ignore[union-attr]

    def test_databricks_connection(self):
        """Test Databricks connection configuration."""
        conn = DestinationConnectionConfig(
            server_hostname_secret_key="DB_HOST",
            http_path_secret_key="DB_PATH",
            access_token_secret_key="DB_TOKEN",
            catalog="test_catalog",
            db_schema="test_schema",
        )
        assert conn.catalog == "test_catalog"
        assert conn.db_schema == "test_schema"


class TestSourceConfig:
    """Tests for SourceConfig model."""

    def test_complete_source_config(self, sample_source_config: dict[str, Any]) -> None:
        """Test complete source configuration."""
        source = SourceConfig(**sample_source_config["source"])
        assert source.name == "test_api"
        assert source.type == "rest_api"
        assert source.environment == Environment.DEV
        assert len(source.resources) == 1
        assert source.resources[0].name == "users"

    def test_source_config_validation(self):
        """Test source configuration validation."""
        with pytest.raises(ValidationError):
            SourceConfig(name="test", type="rest_api")  # type: ignore[call-arg]


class TestDestinationConfig:
    """Tests for DestinationConfig model."""

    def test_complete_destination_config(self, sample_destination_config: dict[str, Any]) -> None:
        """Test complete destination configuration."""
        dest = DestinationConfig(**sample_destination_config["destination"])
        assert dest.name == "test_databricks"
        assert dest.type == "databricks"
        assert dest.environment == Environment.DEV
        assert dest.settings.table_format == "delta"

    def test_destination_default_settings(self):
        """Test destination default settings."""
        dest = DestinationConfig(
            name="test_db",
            type="databricks",  # type: ignore[arg-type]
            environment=Environment.DEV,
            connection=DestinationConnectionConfig(
                server_hostname_secret_key="HOST",
                http_path_secret_key="PATH",
                access_token_secret_key="TOKEN",
            ),
        )
        assert dest.settings.table_format == "delta"  # Default value


class TestScheduleConfig:
    """Tests for ScheduleConfig model."""

    def test_enabled_schedule(self):
        """Test enabled schedule configuration."""
        schedule = ScheduleConfig(enabled=True, cron="0 */6 * * *", timezone="UTC")
        assert schedule.enabled is True
        assert schedule.cron == "0 */6 * * *"
        assert schedule.catchup is False  # default

    def test_disabled_schedule(self):
        """Test disabled schedule configuration."""
        schedule = ScheduleConfig(
            enabled=False, cron="0 0 * * *"  # Still required even if disabled
        )
        assert schedule.enabled is False
        assert schedule.cron == "0 0 * * *"


class TestExecutionConfig:
    """Tests for ExecutionConfig model."""

    def test_default_execution_config(self):
        """Test default execution configuration."""
        exec_config = ExecutionConfig()
        assert exec_config.retries == 2
        assert exec_config.retry_delay == 300
        assert exec_config.timeout == 3600

    def test_custom_execution_config(self):
        """Test custom execution configuration."""
        exec_config = ExecutionConfig(retries=5, retry_delay=120, timeout=7200)
        assert exec_config.retries == 5
        assert exec_config.retry_delay == 120
        assert exec_config.timeout == 7200


class TestMonitoringConfig:
    """Tests for MonitoringConfig model."""

    def test_monitoring_with_metrics(self):
        """Test monitoring configuration with metrics."""
        monitoring = MonitoringConfig(enabled=True, metrics=["duration", "rows_processed"])
        assert monitoring.enabled is True
        assert "duration" in monitoring.metrics

    def test_monitoring_defaults(self):
        """Test monitoring configuration defaults."""
        monitoring = MonitoringConfig()
        assert monitoring.enabled is True
        assert monitoring.metrics == []


class TestPipelineConfig:
    """Tests for PipelineConfig model."""

    def test_complete_pipeline_config(self, sample_pipeline_config: dict[str, Any]) -> None:
        """Test complete pipeline configuration."""
        pipeline = PipelineConfig(**sample_pipeline_config["pipeline"])
        assert pipeline.name == "test_pipeline"
        assert pipeline.environment == Environment.DEV
        assert pipeline.source.config_file == "sources/test_api.yaml"
        assert pipeline.destination.config_file == "destinations/test_databricks.yaml"
        assert pipeline.schedule.enabled is True

    def test_pipeline_without_schedule(self):
        """Test pipeline with required fields."""
        pipeline = PipelineConfig(
            name="test",
            description="Test pipeline",
            environment=Environment.DEV,
            source=PipelineSourceRef(config_file="sources/test.yaml", resources=["users"]),
            destination=PipelineDestinationRef(
                config_file="destinations/test.yaml", dataset_name="test_dataset"
            ),
            schedule=ScheduleConfig(enabled=False, cron="0 0 * * *"),
        )
        assert pipeline.schedule.enabled is False

    def test_pipeline_validation(self):
        """Test pipeline configuration validation."""
        with pytest.raises(ValidationError):
            PipelineConfig(name="test", environment=Environment.DEV)  # type: ignore[call-arg]


class TestSecretsConfig:
    """Tests for SecretsConfig model."""

    def test_secrets_config(self, sample_secrets_config: dict[str, Any]) -> None:
        """Test secrets configuration."""
        secrets = SecretsConfig(**sample_secrets_config)
        assert secrets.environment == Environment.DEV
        assert "TEST_API_KEY_DEV" in secrets.secrets
        assert secrets.secrets["TEST_API_KEY_DEV"].description == "Test API key"
        assert "TEST_API_KEY_DEV" in secrets.validation.required_secrets

    def test_empty_secrets_config(self):
        """Test minimal secrets configuration."""
        from ingestion.config.models import SecretsValidation

        secrets = SecretsConfig(
            environment=Environment.DEV,
            secrets={},
            validation=SecretsValidation(required_secrets=[]),
        )
        assert secrets.environment == Environment.DEV
        assert secrets.secrets == {}
        assert secrets.validation.required_secrets == []
