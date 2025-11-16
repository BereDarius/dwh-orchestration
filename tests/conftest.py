"""Pytest configuration and shared fixtures."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary config directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "config" / "environments" / "dev"
        config_dir.mkdir(parents=True)

        # Create subdirectories
        (config_dir / "sources").mkdir()
        (config_dir / "destinations").mkdir()
        (config_dir / "pipelines").mkdir()

        yield config_dir


@pytest.fixture
def sample_source_config() -> dict[str, Any]:
    """Sample source configuration."""
    return {
        "source": {
            "name": "test_api",
            "type": "rest_api",
            "environment": "dev",
            "connection": {
                "base_url": "https://api.test.com",
                "auth": {
                    "type": "bearer",
                    "credentials_secret_key": "TEST_API_KEY_DEV",
                },
                "timeout": 30,
                "retry": {
                    "max_attempts": 3,
                    "backoff_factor": 2,
                },
            },
            "resources": [
                {
                    "name": "users",
                    "endpoint": "/users",
                    "method": "GET",
                    "params": {},
                    "incremental": {
                        "enabled": True,
                        "cursor_field": "updated_at",
                        "initial_value": "2024-01-01T00:00:00Z",
                    },
                    "primary_key": ["id"],
                    "write_disposition": "merge",
                }
            ],
        }
    }


@pytest.fixture
def sample_destination_config() -> dict[str, Any]:
    """Sample destination configuration."""
    return {
        "destination": {
            "name": "test_databricks",
            "type": "databricks",
            "environment": "dev",
            "connection": {
                "server_hostname_secret_key": "DATABRICKS_HOST_DEV",
                "http_path_secret_key": "DATABRICKS_PATH_DEV",
                "access_token_secret_key": "DATABRICKS_TOKEN_DEV",
                "catalog": "test_catalog",
                "schema": "test_schema",
            },
            "settings": {
                "table_format": "delta",
                "optimize_after_write": True,
                "vacuum_after_write": False,
                "vacuum_retention_hours": 168,
                "merge_parallelism": 4,
            },
        }
    }


@pytest.fixture
def sample_pipeline_config() -> dict[str, Any]:
    """Sample pipeline configuration."""
    return {
        "pipeline": {
            "name": "test_pipeline",
            "description": "Test pipeline",
            "environment": "dev",
            "source": {
                "config_file": "sources/test_api.yaml",
                "resources": ["users"],
                "params": {},
            },
            "destination": {
                "config_file": "destinations/test_databricks.yaml",
                "dataset_name": "test_dataset",
            },
            "schedule": {
                "enabled": True,
                "cron": "0 */6 * * *",
                "timezone": "UTC",
                "catchup": False,
            },
            "execution": {
                "retries": 3,
                "retry_delay": 60,
                "timeout": 3600,
            },
            "monitoring": {
                "sla": {"max_duration_minutes": 60},
                "alerts": {
                    "on_failure": True,
                    "on_success": False,
                    "on_retry": False,
                },
            },
        }
    }


@pytest.fixture
def sample_secrets_config() -> dict[str, Any]:
    """Sample secrets configuration."""
    return {
        "environment": "dev",
        "secrets": {
            "TEST_API_KEY_DEV": {
                "github_secret": "TEST_API_KEY_DEV",
                "description": "Test API key",
                "required": True,
            },
            "DATABRICKS_HOST_DEV": {
                "github_secret": "DATABRICKS_HOST_DEV",
                "description": "Databricks hostname",
                "required": True,
            },
        },
        "validation": {
            "required_secrets": ["TEST_API_KEY_DEV", "DATABRICKS_HOST_DEV"],
            "patterns": {"TEST_API_KEY_DEV": "^[a-zA-Z0-9_-]+$"},
        },
    }


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up mock environment variables."""
    env_vars = {
        "ENVIRONMENT": "dev",
        "TEST_API_KEY_DEV": "test-key-12345",
        "DATABRICKS_HOST_DEV": "test.databricks.com",
        "DATABRICKS_PATH_DEV": "/sql/1.0/warehouses/test",
        "DATABRICKS_TOKEN_DEV": "dapi1234567890",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def config_files(
    temp_config_dir: Path,
    sample_source_config: dict[str, Any],
    sample_destination_config: dict[str, Any],
    sample_pipeline_config: dict[str, Any],
    sample_secrets_config: dict[str, Any],
) -> Path:
    """Create sample config files in temp directory."""
    # Write source config
    source_file = temp_config_dir / "sources" / "test_api.yaml"
    with open(source_file, "w") as f:
        yaml.dump(sample_source_config, f)

    # Write destination config
    dest_file = temp_config_dir / "destinations" / "test_databricks.yaml"
    with open(dest_file, "w") as f:
        yaml.dump(sample_destination_config, f)

    # Write pipeline config
    pipeline_file = temp_config_dir / "pipelines" / "test_pipeline.yaml"
    with open(pipeline_file, "w") as f:
        yaml.dump(sample_pipeline_config, f)

    # Write secrets config
    secrets_file = temp_config_dir / "secrets_mapping.yaml"
    with open(secrets_file, "w") as f:
        yaml.dump(sample_secrets_config, f)

    return temp_config_dir
