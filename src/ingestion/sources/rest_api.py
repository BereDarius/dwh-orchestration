"""REST API source implementation."""

from typing import Any, Dict, Iterator, List, Optional

import dlt
from dlt.extract.resource import DltResource
from dlt.sources.rest_api import rest_api_resources

from ingestion.config.models import ResourceConfig, SourceConfig
from ingestion.sources.base import BaseSource
from ingestion.utils.logging import get_logger

logger = get_logger(__name__)


class RestApiSource(BaseSource):
    """REST API data source using DLT's rest_api source."""

    def create_resources(
        self,
        resource_names: List[str],
    ) -> Iterator[DltResource]:
        """
        Create DLT resources for REST API endpoints.

        Args:
            resource_names: Names of resources to create

        Yields:
            DLT resources
        """
        for resource_name in resource_names:
            resource_config = self.get_resource_config(resource_name)
            logger.info(f"Creating REST API resource: {resource_name}")

            # Build DLT rest_api configuration
            rest_api_config = self._build_rest_api_config(resource_config)

            # Create resource using DLT's rest_api_resources
            for resource in rest_api_resources(rest_api_config):
                # Apply write disposition (write_disposition always has default value APPEND,
                # so this condition is always True - branch 42->48 is unreachable)
                if resource_config.write_disposition:  # pragma: no branch
                    resource = resource.apply_hints(
                        write_disposition=resource_config.write_disposition.value
                    )

                # Apply primary key
                if resource_config.primary_key:
                    resource = resource.apply_hints(primary_key=resource_config.primary_key)

                yield resource

    def _build_rest_api_config(self, resource_config: ResourceConfig) -> Dict[str, Any]:
        """
        Build DLT rest_api configuration from resource config.

        Args:
            resource_config: Resource configuration

        Returns:
            DLT rest_api configuration dictionary
        """
        config: Dict[str, Any] = {
            "client": {
                "base_url": self.config.connection.base_url,
            },
            "resources": [
                {
                    "name": resource_config.name,
                    "endpoint": {
                        "path": resource_config.endpoint,
                        "method": resource_config.method,
                        "params": self._resolve_params(resource_config.params),
                    },
                }
            ],
        }

        # Add authentication if configured
        if self.config.connection.auth:
            auth_config = self._build_auth_config()
            # auth_config is always non-None here since _build_auth_config() only returns
            # None if auth is not configured (which we already checked above)
            if auth_config:  # pragma: no branch
                config["client"]["auth"] = auth_config

        # Add incremental loading if configured
        if resource_config.incremental and resource_config.incremental.enabled:
            config["resources"][0]["endpoint"]["incremental"] = {
                "cursor_path": resource_config.incremental.cursor_field,
                "initial_value": resource_config.incremental.initial_value,
            }

        return config

    def _build_auth_config(self) -> Optional[Dict[str, Any]]:
        """
        Build authentication configuration.

        Returns:
            Authentication configuration or None
        """
        if not self.config.connection.auth:
            return None

        auth = self.config.connection.auth
        auth_config: Dict[str, Any] = {
            "type": auth.type.value,
        }

        # Add credentials based on auth type
        if auth.type.value == "bearer" and auth.credentials_secret_key:
            auth_config["token"] = auth.credentials_secret_key

        elif auth.type.value == "api_key" and auth.credentials_secret_key:
            auth_config["api_key"] = auth.credentials_secret_key

        elif auth.type.value == "basic":
            if auth.username_secret_key and auth.password_secret_key:
                auth_config["username"] = auth.username_secret_key
                auth_config["password"] = auth.password_secret_key

        return auth_config

    def _resolve_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve parameter placeholders with runtime values.

        Args:
            params: Parameter dictionary with potential placeholders

        Returns:
            Resolved parameters
        """
        resolved = {}

        for key, value in params.items():
            if isinstance(value, str):
                # Replace placeholders like {channel_id} with runtime params
                resolved_value = value
                for param_key, param_value in self.params.items():
                    placeholder = f"{{{param_key}}}"
                    if placeholder in resolved_value:
                        resolved_value = resolved_value.replace(placeholder, str(param_value))
                resolved[key] = resolved_value
            else:
                resolved[key] = value

        return resolved
