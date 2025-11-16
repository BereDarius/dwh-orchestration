"""Unit tests for configuration loader."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from ingestion.config.loader import ConfigLoader
from ingestion.config.models import Environment


class TestConfigLoader:
    """Tests for ConfigLoader class."""

    def test_init_with_environment(self) -> None:
        """Test ConfigLoader initialization with environment."""
        loader = ConfigLoader(environment=Environment.DEV)
        assert loader.environment == Environment.DEV
        assert loader.config_path.name == "dev"

    def test_init_with_string_environment(self) -> None:
        """Test ConfigLoader initialization with string environment."""
        loader = ConfigLoader(environment="dev")
        assert loader.environment == Environment.DEV

    @patch("ingestion.config.environment.get_environment")
    def test_init_with_no_environment(self, mock_get_env: MagicMock) -> None:
        """Test ConfigLoader initialization without environment."""
        mock_get_env.return_value = Environment.DEV
        loader = ConfigLoader()
        assert loader.environment == Environment.DEV

    def test_load_yaml(self) -> None:
        """Test loading YAML file."""
        loader = ConfigLoader(environment=Environment.DEV)

        yaml_content = "key: value\nlist:\n  - item1\n  - item2"
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with patch("pathlib.Path.exists", return_value=True):
                # Use type: ignore for accessing protected member in tests
                data = loader._load_yaml(Path("/test/file.yaml"))  # type: ignore[attr-defined]
                assert data["key"] == "value"
                assert len(data["list"]) == 2

    def test_load_yaml_file_not_found(self) -> None:
        """Test loading non-existent YAML file."""
        loader = ConfigLoader(environment=Environment.DEV)

        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                # Use type: ignore for accessing protected member in tests
                loader._load_yaml(Path("/nonexistent/file.yaml"))  # type: ignore[attr-defined]

    def test_load_yaml_invalid(self) -> None:
        """Test loading invalid YAML file."""
        loader = ConfigLoader(environment=Environment.DEV)

        invalid_yaml = "invalid: yaml: content: {"
        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with patch("pathlib.Path.exists", return_value=True):
                with pytest.raises(yaml.YAMLError):
                    # Use type: ignore for accessing protected member in tests
                    loader._load_yaml(Path("/test/invalid.yaml"))  # type: ignore[attr-defined]

    def test_load_source_config(self, tmp_path: Path) -> None:
        """Test loading source configuration."""
        # Create test config file
        config_dir = tmp_path / "config" / "environments" / "dev" / "sources"
        config_dir.mkdir(parents=True)

        source_config: dict[str, Any] = {  # type: ignore[misc]
            "source": {
                "name": "test_source",
                "type": "rest_api",
                "environment": "dev",
                "base_url": "https://api.example.com",
                "connection": {"base_url": "https://api.example.com"},
                "auth": {"type": "bearer", "credentials_secret_key": "API_TOKEN"},
                "resources": [],
            }
        }

        config_file = config_dir / "test_source.yaml"
        config_file.write_text(yaml.dump(source_config))

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            source = loader.load_source_config("test_source.yaml")

            assert source.name == "test_source"
            assert source.type == "rest_api"

    def test_load_destination_config(self, tmp_path: Path) -> None:
        """Test loading destination configuration."""
        config_dir = tmp_path / "config" / "environments" / "dev" / "destinations"
        config_dir.mkdir(parents=True)

        dest_config: dict[str, Any] = {  # type: ignore[misc]
            "destination": {
                "name": "test_dest",
                "type": "databricks",
                "environment": "dev",
                "connection": {
                    "server_hostname_secret_key": "DB_HOST",
                    "http_path_secret_key": "DB_PATH",
                    "access_token_secret_key": "DB_TOKEN",
                    "catalog": "main",
                },
                "settings": {},
            }
        }

        config_file = config_dir / "test_dest.yaml"
        config_file.write_text(yaml.dump(dest_config))

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            dest = loader.load_destination_config("test_dest.yaml")

            assert dest.name == "test_dest"
            assert dest.type == "databricks"

    def test_load_pipeline_config(self, tmp_path: Path) -> None:
        """Test loading pipeline configuration."""
        config_dir = tmp_path / "config" / "environments" / "dev" / "pipelines"
        config_dir.mkdir(parents=True)

        pipeline_config: dict[str, Any] = {  # type: ignore[misc]
            "pipeline": {
                "name": "test_pipeline",
                "environment": "dev",
                "source": {"config_file": "test_source.yaml", "resources": []},
                "destination": {"config_file": "test_dest.yaml", "dataset_name": "test_dataset"},
                "schedule": {"cron": "0 0 * * *"},
                "execution": {},
                "transformations": {},
                "monitoring": {},
                "alerts": {},
            }
        }

        config_file = config_dir / "test_pipeline.yaml"
        config_file.write_text(yaml.dump(pipeline_config))

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            pipeline = loader.load_pipeline_config("test_pipeline.yaml")

            assert pipeline.name == "test_pipeline"
            assert pipeline.source.config_file == "test_source.yaml"

    def test_load_all_sources(self, tmp_path: Path) -> None:
        """Test loading all source configurations."""
        config_dir = tmp_path / "config" / "environments" / "dev" / "sources"
        config_dir.mkdir(parents=True)

        # Create multiple source configs
        for i in range(2):
            source_config: dict[str, Any] = {  # type: ignore[misc]
                "source": {
                    "name": f"source_{i}",
                    "type": "rest_api",
                    "environment": "dev",
                    "base_url": f"https://api{i}.example.com",
                    "connection": {"base_url": f"https://api{i}.example.com"},
                    "auth": {"type": "bearer"},
                    "resources": [],
                }
            }
            config_file = config_dir / f"source_{i}.yaml"
            config_file.write_text(yaml.dump(source_config))

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            sources = loader.load_all_sources()

            assert len(sources) == 2
            assert "source_0" in sources
            assert "source_1" in sources

    def test_load_all_sources_empty_dir(self, tmp_path: Path) -> None:
        """Test loading sources when directory doesn't exist."""
        # Create env dir but not sources dir
        env_dir = tmp_path / "config" / "environments" / "dev"
        env_dir.mkdir(parents=True)

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            sources = loader.load_all_sources()

            assert sources == {}

    def test_load_all_destinations(self, tmp_path: Path) -> None:
        """Test loading all destination configurations."""
        config_dir = tmp_path / "config" / "environments" / "dev" / "destinations"
        config_dir.mkdir(parents=True)

        dest_config: dict[str, Any] = {  # type: ignore[misc]
            "destination": {
                "name": "dest_0",
                "type": "databricks",
                "environment": "dev",
                "connection": {
                    "server_hostname_secret_key": "DB_HOST",
                    "http_path_secret_key": "DB_PATH",
                    "access_token_secret_key": "DB_TOKEN",
                    "catalog": "main",
                },
                "settings": {},
            }
        }
        config_file = config_dir / "dest_0.yaml"
        config_file.write_text(yaml.dump(dest_config))

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            dests = loader.load_all_destinations()

            assert len(dests) == 1
            assert "dest_0" in dests

    def test_load_all_pipelines(self, tmp_path: Path) -> None:
        """Test loading all pipeline configurations."""
        config_dir = tmp_path / "config" / "environments" / "dev" / "pipelines"
        config_dir.mkdir(parents=True)

        pipeline_config: dict[str, Any] = {  # type: ignore[misc]
            "pipeline": {
                "name": "pipeline_0",
                "environment": "dev",
                "source": {"config_file": "test_source.yaml", "resources": []},
                "destination": {"config_file": "test_dest.yaml", "dataset_name": "test_dataset"},
                "schedule": {"cron": "0 0 * * *"},
                "execution": {},
                "transformations": {},
                "monitoring": {},
                "alerts": {},
            }
        }
        config_file = config_dir / "pipeline_0.yaml"
        config_file.write_text(yaml.dump(pipeline_config))

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            pipelines = loader.load_all_pipelines()

            assert len(pipelines) == 1
            assert "pipeline_0" in pipelines

    def test_discover_all_configs(self, tmp_path: Path) -> None:
        """Test discovering all configurations."""
        # Create all config directories
        for dir_name in ["sources", "destinations", "pipelines"]:
            config_dir = tmp_path / "config" / "environments" / "dev" / dir_name
            config_dir.mkdir(parents=True)

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            all_configs = loader.discover_all_configs()

            assert "sources" in all_configs
            assert "destinations" in all_configs
            assert "pipelines" in all_configs

    def test_get_pipeline_files(self, tmp_path: Path) -> None:
        """Test getting pipeline file list."""
        config_dir = tmp_path / "config" / "environments" / "dev" / "pipelines"
        config_dir.mkdir(parents=True)

        (config_dir / "pipeline1.yaml").touch()
        (config_dir / "pipeline2.yaml").touch()

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            files = loader.get_pipeline_files()

            assert len(files) == 2
            assert "pipeline1.yaml" in files

    def test_get_source_files(self, tmp_path: Path) -> None:
        """Test getting source file list."""
        config_dir = tmp_path / "config" / "environments" / "dev" / "sources"
        config_dir.mkdir(parents=True)

        (config_dir / "source1.yaml").touch()

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            files = loader.get_source_files()

            assert len(files) == 1
            assert "source1.yaml" in files

    def test_get_destination_files(self, tmp_path: Path) -> None:
        """Test getting destination file list."""
        config_dir = tmp_path / "config" / "environments" / "dev" / "destinations"
        config_dir.mkdir(parents=True)

        (config_dir / "dest1.yaml").touch()

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            files = loader.get_destination_files()

            assert len(files) == 1
            assert "dest1.yaml" in files

    def test_get_files_empty_directory(self, tmp_path: Path) -> None:
        """Test getting files when directories don't exist."""
        # Create env dir but not sub-dirs
        env_dir = tmp_path / "config" / "environments" / "dev"
        env_dir.mkdir(parents=True)

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)

            assert loader.get_pipeline_files() == []
            assert loader.get_source_files() == []
            assert loader.get_destination_files() == []

    def test_load_source_config_invalid(self, tmp_path: Path) -> None:
        """Test loading invalid source configuration."""
        config_dir = tmp_path / "config" / "environments" / "dev" / "sources"
        config_dir.mkdir(parents=True)

        # Missing required fields
        source_config: dict[str, Any] = {"source": {"name": "test"}}  # type: ignore[misc]

        config_file = config_dir / "invalid.yaml"
        config_file.write_text(yaml.dump(source_config))

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            with pytest.raises(ValueError, match="Invalid source configuration"):
                loader.load_source_config("invalid.yaml")

    def test_load_destination_config_invalid(self, tmp_path: Path) -> None:
        """Test loading invalid destination configuration."""
        config_dir = tmp_path / "config" / "environments" / "dev" / "destinations"
        config_dir.mkdir(parents=True)

        dest_config: dict[str, Any] = {"destination": {"name": "test"}}  # type: ignore[misc]

        config_file = config_dir / "invalid.yaml"
        config_file.write_text(yaml.dump(dest_config))

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            with pytest.raises(ValueError, match="Invalid destination configuration"):
                loader.load_destination_config("invalid.yaml")

    def test_load_pipeline_config_invalid(self, tmp_path: Path) -> None:
        """Test loading invalid pipeline configuration."""
        config_dir = tmp_path / "config" / "environments" / "dev" / "pipelines"
        config_dir.mkdir(parents=True)

        pipeline_config: dict[str, Any] = {"pipeline": {"name": "test"}}  # type: ignore[misc]

        config_file = config_dir / "invalid.yaml"
        config_file.write_text(yaml.dump(pipeline_config))

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            with pytest.raises(ValueError, match="Invalid pipeline configuration"):
                loader.load_pipeline_config("invalid.yaml")

    def test_load_all_sources_with_error(self, tmp_path: Path) -> None:
        """Test loading sources with one invalid config."""
        config_dir = tmp_path / "config" / "environments" / "dev" / "sources"
        config_dir.mkdir(parents=True)

        # Valid source
        valid_config: dict[str, Any] = {  # type: ignore[misc]
            "source": {
                "name": "valid_source",
                "type": "rest_api",
                "environment": "dev",
                "connection": {"base_url": "https://api.example.com"},
                "resources": [],
            }
        }
        (config_dir / "valid.yaml").write_text(yaml.dump(valid_config))

        # Invalid source
        invalid_config: dict[str, Any] = {"source": {"name": "invalid"}}  # type: ignore[misc]
        (config_dir / "invalid.yaml").write_text(yaml.dump(invalid_config))

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            # Should continue loading despite error
            sources = loader.load_all_sources()

            # Only valid source should be loaded
            assert len(sources) == 1
            assert "valid_source" in sources

    def test_load_all_destinations_with_error(self, tmp_path: Path) -> None:
        """Test loading destinations with one invalid config."""
        config_dir = tmp_path / "config" / "environments" / "dev" / "destinations"
        config_dir.mkdir(parents=True)

        # Invalid destination
        invalid_config: dict[str, Any] = {"destination": {"name": "invalid"}}  # type: ignore[misc]
        (config_dir / "invalid.yaml").write_text(yaml.dump(invalid_config))

        with patch(
            "ingestion.config.environment.get_config_base_path", return_value=tmp_path / "config"
        ):
            loader = ConfigLoader(environment=Environment.DEV)
            dests = loader.load_all_destinations()

            # No destinations should be loaded due to validation error
            assert len(dests) == 0
