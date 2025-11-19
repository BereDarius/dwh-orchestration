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
    Get the configuration path (same for all environments).
    Environment is now controlled via ENVIRONMENT variable, not directory structure.

    Args:
        environment: Environment to get config for (ignored, kept for compatibility)

    Returns:
        Path: Configuration directory path
    """
    base_path = get_config_base_path()

    if not base_path.exists():
        raise FileNotFoundError(f"Configuration directory not found: {base_path}")

    return base_path


def load_environment_config(config_type: str, filename: str) -> Path:
    """
    Load configuration file.
    Environment is now controlled via ENVIRONMENT variable, not directory structure.

    Args:
        config_type: Type of config (sources, destinations, pipelines, jobs, triggers)
        filename: Name of the configuration file

    Returns:
        Path: Path to the configuration file

    Raises:
        FileNotFoundError: If configuration file doesn't exist
    """
    base_path = get_config_base_path()
    config_path = base_path / config_type / filename

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    return config_path
