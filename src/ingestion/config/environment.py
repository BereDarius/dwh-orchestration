"""Environment management utilities."""

import os
from pathlib import Path

from ingestion.config.models import Environment


def get_environment() -> Environment:
    """
    Get the current environment from environment variable.

    Returns:
        Environment: Current environment (dev, stage, or prod)

    Raises:
        ValueError: If ENVIRONMENT variable is not set or invalid
    """
    env_str = os.getenv("ENVIRONMENT")

    if not env_str:
        raise ValueError("ENVIRONMENT variable not set. Must be one of: dev, stage, prod")

    try:
        return Environment(env_str.lower())
    except ValueError as e:
        raise ValueError(f"Invalid ENVIRONMENT: {env_str}. Must be one of: dev, stage, prod") from e


def get_config_base_path() -> Path:
    """
    Get the base path for configuration files.

    Returns:
        Path: Base configuration directory path
    """
    # Assume config is in project root/config
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    return project_root / "config"


def get_environment_config_path(environment: Environment | None = None) -> Path:
    """
    Get the configuration path for a specific environment.

    Args:
        environment: Environment to get config for (defaults to current environment)

    Returns:
        Path: Environment-specific configuration directory path
    """
    if environment is None:
        environment = get_environment()

    base_path = get_config_base_path()
    env_path = base_path / "environments" / environment.value

    if not env_path.exists():
        raise FileNotFoundError(
            f"Configuration directory not found for environment {environment.value}: {env_path}"
        )

    return env_path


def load_environment_config(config_type: str, filename: str) -> Path:
    """
    Load configuration file for current environment.

    Args:
        config_type: Type of config (sources, destinations, pipelines)
        filename: Name of the configuration file

    Returns:
        Path: Path to the configuration file

    Raises:
        FileNotFoundError: If configuration file doesn't exist
    """
    env_path = get_environment_config_path()
    config_path = env_path / config_type / filename

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    return config_path
