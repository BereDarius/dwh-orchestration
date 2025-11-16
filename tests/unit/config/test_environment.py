"""Unit tests for environment utilities."""

from pathlib import Path

import pytest

from ingestion.config.environment import (
    get_config_base_path,
    get_environment,
    get_environment_config_path,
    load_environment_config,
)
from ingestion.config.models import Environment


class TestGetEnvironment:
    """Tests for get_environment function."""

    def test_get_environment_dev(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting dev environment."""
        monkeypatch.setenv("ENVIRONMENT", "dev")
        env = get_environment()
        assert env == Environment.DEV

    def test_get_environment_stage(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting stage environment."""
        monkeypatch.setenv("ENVIRONMENT", "stage")
        env = get_environment()
        assert env == Environment.STAGE

    def test_get_environment_prod(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting prod environment."""
        monkeypatch.setenv("ENVIRONMENT", "prod")
        env = get_environment()
        assert env == Environment.PROD

    def test_get_environment_uppercase(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment variable is case-insensitive."""
        monkeypatch.setenv("ENVIRONMENT", "DEV")
        env = get_environment()
        assert env == Environment.DEV

    def test_get_environment_not_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test error when ENVIRONMENT not set."""
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        with pytest.raises(ValueError, match="ENVIRONMENT variable not set"):
            get_environment()

    def test_get_environment_invalid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test error when ENVIRONMENT has invalid value."""
        monkeypatch.setenv("ENVIRONMENT", "invalid")
        with pytest.raises(ValueError, match="Invalid ENVIRONMENT"):
            get_environment()


class TestGetConfigBasePath:
    """Tests for get_config_base_path function."""

    def test_get_config_base_path(self) -> None:
        """Test getting base config path."""
        base_path = get_config_base_path()
        assert isinstance(base_path, Path)
        assert base_path.name == "config"
        # Should point to project root/config
        assert (base_path.parent / "src").exists()


class TestGetEnvironmentConfigPath:
    """Tests for get_environment_config_path function."""

    def test_get_environment_config_path_default(
        self, monkeypatch: pytest.MonkeyPatch, temp_config_dir: Path
    ) -> None:
        """Test getting config path for current environment."""
        # Mock get_environment to return dev
        monkeypatch.setenv("ENVIRONMENT", "dev")

        # Mock get_config_base_path to return temp directory
        import ingestion.config.environment as env_module

        monkeypatch.setattr(
            env_module, "get_config_base_path", lambda: temp_config_dir.parent.parent
        )

        path = get_environment_config_path()
        assert path.name == "dev"
        assert path.parent.name == "environments"

    def test_get_environment_config_path_explicit(
        self, monkeypatch: pytest.MonkeyPatch, temp_config_dir: Path
    ) -> None:
        """Test getting config path for explicit environment."""
        # Mock get_config_base_path to return temp directory
        import ingestion.config.environment as env_module

        monkeypatch.setattr(
            env_module, "get_config_base_path", lambda: temp_config_dir.parent.parent
        )

        path = get_environment_config_path(Environment.DEV)
        assert path.name == "dev"
        assert path.exists()

    def test_get_environment_config_path_not_found(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test error when environment config directory doesn't exist."""
        # Mock get_config_base_path to return a non-existent path
        import ingestion.config.environment as env_module

        monkeypatch.setattr(env_module, "get_config_base_path", lambda: tmp_path)

        with pytest.raises(FileNotFoundError, match="Configuration directory not found"):
            get_environment_config_path(Environment.DEV)


class TestLoadEnvironmentConfig:
    """Tests for load_environment_config function."""

    def test_load_environment_config_success(
        self, monkeypatch: pytest.MonkeyPatch, config_files: Path
    ) -> None:
        """Test loading existing config file."""
        # Mock get_environment_config_path to return our temp directory
        import ingestion.config.environment as env_module

        monkeypatch.setattr(env_module, "get_environment_config_path", lambda: config_files)

        config_path = load_environment_config("sources", "test_api.yaml")
        assert config_path.exists()
        assert config_path.name == "test_api.yaml"
        assert config_path.parent.name == "sources"

    def test_load_environment_config_not_found(
        self, monkeypatch: pytest.MonkeyPatch, config_files: Path
    ) -> None:
        """Test error when config file doesn't exist."""
        # Mock get_environment_config_path to return our temp directory
        import ingestion.config.environment as env_module

        monkeypatch.setattr(env_module, "get_environment_config_path", lambda: config_files)

        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            load_environment_config("sources", "nonexistent.yaml")
