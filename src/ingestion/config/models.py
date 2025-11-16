"""Pydantic models for configuration validation."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Environment(str, Enum):
    """Supported environments."""

    DEV = "dev"
    STAGE = "stage"
    PROD = "prod"


class AuthType(str, Enum):
    """Supported authentication types."""

    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"


class SourceType(str, Enum):
    """Supported source types."""

    REST_API = "rest_api"
    DATABASE = "database"
    FILE = "file"
    STREAM = "stream"


class DestinationType(str, Enum):
    """Supported destination types."""

    DATABRICKS = "databricks"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    POSTGRES = "postgres"
    DUCKDB = "duckdb"


class WriteDisposition(str, Enum):
    """Write disposition for DLT."""

    APPEND = "append"
    REPLACE = "replace"
    MERGE = "merge"


class DataType(str, Enum):
    """Supported data types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    DATE = "date"
    JSON = "json"


class CheckType(str, Enum):
    """Data quality check types."""

    NOT_NULL = "not_null"
    UNIQUE = "unique"
    POSITIVE = "positive"
    RANGE = "range"
    PATTERN = "pattern"
    FRESHNESS = "freshness"
    COMPLETENESS = "completeness"
    VOLUME = "volume"
    SCHEMA = "schema"


class RetryConfig(BaseModel):
    """Retry configuration."""

    max_attempts: int = Field(default=3, ge=1, le=10)
    backoff_factor: float = Field(default=2.0, ge=1.0)
    backoff_max: int = Field(default=60, ge=1)


class AuthConfig(BaseModel):
    """Authentication configuration."""

    type: AuthType
    credentials_secret_key: str | None = None
    username_secret_key: str | None = None
    password_secret_key: str | None = None
    token_secret_key: str | None = None


class ConnectionConfig(BaseModel):
    """Connection configuration."""

    base_url: str | None = None
    auth: AuthConfig | None = None
    timeout: int = Field(default=30, ge=1)
    retry: RetryConfig = Field(default_factory=RetryConfig)


class ColumnSchema(BaseModel):
    """Column schema definition."""

    name: str
    data_type: DataType
    nullable: bool = True
    description: str | None = None
    primary_key: bool = False


class DataQualityCheck(BaseModel):
    """Data quality check definition."""

    type: CheckType
    columns: list[str] | None = None
    column: str | None = None
    min_value: int | float | None = None
    max_value: int | float | None = None
    pattern: str | None = None
    max_age_hours: int | None = None
    min_rows: int | None = None
    max_rows: int | None = None
    required_columns: list[str] | None = None
    severity: str = "error"


class IncrementalConfig(BaseModel):
    """Incremental loading configuration."""

    enabled: bool = True
    strategy: str = "append"
    cursor_field: str
    initial_value: str


class ResourceConfig(BaseModel):
    """Source resource configuration."""

    name: str
    description: str | None = None
    endpoint: str | None = None
    method: str = "GET"
    params: dict[str, Any] = Field(default_factory=dict)
    incremental: IncrementalConfig | None = None
    primary_key: list[str] = Field(default_factory=list)
    write_disposition: WriteDisposition = WriteDisposition.APPEND
    table_schema: dict[str, Any] | None = None
    data_quality: dict[str, Any] | None = None
    pii_fields: list[str] = Field(default_factory=list)
    aliases: dict[str, str] = Field(default_factory=dict)


class SourceConfig(BaseModel):
    """Source configuration."""

    name: str
    type: SourceType
    description: str | None = None
    environment: Environment
    connection: ConnectionConfig
    resources: list[ResourceConfig]


class DestinationConnectionConfig(BaseModel):
    """Destination connection configuration."""

    server_hostname_secret_key: str | None = None
    http_path_secret_key: str | None = None
    access_token_secret_key: str | None = None
    catalog: str | None = None
    db_schema: str = "raw_data"
    session_configuration: dict[str, str] = Field(default_factory=dict)
    timeout: int = Field(default=300, ge=1)
    retry: RetryConfig = Field(default_factory=RetryConfig)


class DestinationSettings(BaseModel):
    """Destination settings."""

    table_format: str = "delta"
    partition_by: list[str] = Field(default_factory=list)
    cluster_by: list[str] = Field(default_factory=list)
    write_mode: str = "append"
    optimize_after_write: bool = True
    vacuum_after_write: bool = False
    vacuum_retention_hours: int = 168
    schema_evolution: bool = True
    case_sensitive: bool = False
    max_parallel_loads: int = 4
    batch_size: int = 10000


class NamingConvention(BaseModel):
    """Naming convention configuration."""

    prefix: str = ""
    suffix: str = ""
    case: str = "snake_case"


class DataRetention(BaseModel):
    """Data retention configuration."""

    enabled: bool = False
    days: int = 7


class DestinationConfig(BaseModel):
    """Destination configuration."""

    name: str
    type: DestinationType
    description: str | None = None
    environment: Environment
    connection: DestinationConnectionConfig
    settings: DestinationSettings = Field(default_factory=DestinationSettings)
    naming: NamingConvention = Field(default_factory=NamingConvention)
    data_retention: DataRetention = Field(default_factory=DataRetention)


class ScheduleConfig(BaseModel):
    """Pipeline schedule configuration."""

    enabled: bool = True
    cron: str
    timezone: str = "UTC"
    catchup: bool = False
    max_active_runs: int = 1


class ExecutionConfig(BaseModel):
    """Pipeline execution configuration."""

    parallelism: int = Field(default=2, ge=1)
    timeout: int = Field(default=3600, ge=60)
    retries: int = Field(default=2, ge=0)
    retry_delay: int = Field(default=300, ge=0)
    max_memory_mb: int = Field(default=2048, ge=512)
    max_cpu_cores: int = Field(default=2, ge=1)


class TransformationsConfig(BaseModel):
    """Transformations configuration."""

    enabled: bool = False


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""

    enabled: bool = True
    metrics: list[str] = Field(default_factory=list)


class AlertChannel(BaseModel):
    """Alert channel configuration."""

    type: str
    recipients: list[str] | None = None
    webhook_secret_key: str | None = None


class AlertsConfig(BaseModel):
    """Alerts configuration."""

    enabled: bool = False
    channels: list[AlertChannel] = Field(default_factory=list)  # type: ignore[misc]
    on_failure: bool = True
    on_success: bool = False
    on_sla_miss: bool = False


class PipelineSourceRef(BaseModel):
    """Reference to source configuration."""

    config_file: str
    resources: list[str]
    params: dict[str, Any] = Field(default_factory=dict)


class PipelineDestinationRef(BaseModel):
    """Reference to destination configuration."""

    config_file: str
    dataset_name: str


class PipelineConfig(BaseModel):
    """Pipeline configuration."""

    name: str
    description: str | None = None
    environment: Environment
    source: PipelineSourceRef
    destination: PipelineDestinationRef
    schedule: ScheduleConfig
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    transformations: TransformationsConfig = Field(default_factory=TransformationsConfig)
    data_quality: dict[str, Any] | None = None
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)
    tags: list[str] = Field(default_factory=list)
    owner: str = "data-engineering"
    sla_hours: int = 24


class SecretMapping(BaseModel):
    """Secret mapping configuration."""

    github_secret: str
    description: str
    required: bool = True


class SecretsValidation(BaseModel):
    """Secrets validation configuration."""

    required_secrets: list[str]
    patterns: dict[str, str] = Field(default_factory=dict)


class SecretsConfig(BaseModel):
    """Secrets configuration."""

    environment: Environment
    secrets: dict[str, SecretMapping]
    validation: SecretsValidation
