"""Tests for pipeline factory."""

from unittest.mock import MagicMock, patch

from ingestion.config.models import DestinationType, Environment
from ingestion.pipelines.factory import PipelineFactory


class TestPipelineFactory:
    """Test PipelineFactory class."""

    @patch("ingestion.pipelines.factory.ConfigLoader")
    def test_init_default_environment(self, mock_config_loader_class: MagicMock) -> None:
        """Test initialization with default environment."""
        mock_loader_instance = MagicMock()
        mock_loader_instance.environment = Environment.DEV
        mock_config_loader_class.return_value = mock_loader_instance

        factory = PipelineFactory()

        mock_config_loader_class.assert_called_once_with(None)
        assert factory.config_loader == mock_loader_instance
        assert factory.environment == Environment.DEV

    @patch("ingestion.pipelines.factory.ConfigLoader")
    def test_init_with_environment(self, mock_config_loader_class: MagicMock) -> None:
        """Test initialization with specific environment."""
        mock_loader_instance = MagicMock()
        mock_loader_instance.environment = Environment.PROD
        mock_config_loader_class.return_value = mock_loader_instance

        factory = PipelineFactory(environment=Environment.PROD)

        mock_config_loader_class.assert_called_once_with(Environment.PROD)
        assert factory.environment == Environment.PROD

    @patch("ingestion.pipelines.factory.dlt.pipeline")
    @patch("ingestion.pipelines.factory.ConfigLoader")
    def test_create_pipeline_with_provided_configs(
        self,
        mock_config_loader_class: MagicMock,
        mock_dlt_pipeline: MagicMock,
    ) -> None:
        """Test creating pipeline with all configs provided."""
        mock_loader = MagicMock()
        mock_config_loader_class.return_value = mock_loader
        mock_pipeline_inst = MagicMock()
        mock_dlt_pipeline.return_value = mock_pipeline_inst

        # Create mock configs
        mock_pipeline_config = MagicMock()
        mock_pipeline_config.name = "test_pipeline"
        mock_pipeline_config.destination.dataset_name = "test_dataset"
        mock_pipeline_config.source.config_file = "test_source.yaml"
        mock_pipeline_config.destination.config_file = "test_destination.yaml"

        mock_source_config = MagicMock()
        mock_destination_config = MagicMock()
        mock_destination_config.type.value = "duckdb"

        factory = PipelineFactory()
        result = factory.create_pipeline(
            mock_pipeline_config,
            mock_source_config,
            mock_destination_config,
        )

        # Should not load configs since they were provided
        mock_loader.load_source_config.assert_not_called()
        mock_loader.load_destination_config.assert_not_called()

        # Should create DLT pipeline
        mock_dlt_pipeline.assert_called_once_with(
            pipeline_name="test_pipeline",
            destination="duckdb",
            dataset_name="test_dataset",
            progress="log",
        )
        assert result == mock_pipeline_inst

    @patch("ingestion.pipelines.factory.dlt.pipeline")
    @patch("ingestion.pipelines.factory.ConfigLoader")
    def test_create_pipeline_load_source_config(
        self,
        mock_config_loader_class: MagicMock,
        mock_dlt_pipeline: MagicMock,
    ) -> None:
        """Test creating pipeline loads source config if not provided."""
        mock_loader = MagicMock()
        mock_source_config = MagicMock()
        mock_loader.load_source_config.return_value = mock_source_config
        mock_config_loader_class.return_value = mock_loader
        mock_pipeline_inst = MagicMock()
        mock_dlt_pipeline.return_value = mock_pipeline_inst

        mock_pipeline_config = MagicMock()
        mock_pipeline_config.source.config_file = "test_source.yaml"
        mock_pipeline_config.destination.config_file = "test_destination.yaml"
        mock_destination_config = MagicMock()
        mock_destination_config.type.value = "duckdb"

        factory = PipelineFactory()
        factory.create_pipeline(
            mock_pipeline_config,
            source_config=None,  # Not provided
            destination_config=mock_destination_config,
        )

        mock_loader.load_source_config.assert_called_once_with("test_source.yaml")

    @patch("ingestion.pipelines.factory.dlt.pipeline")
    @patch("ingestion.pipelines.factory.ConfigLoader")
    def test_create_pipeline_load_destination_config(
        self,
        mock_config_loader_class: MagicMock,
        mock_dlt_pipeline: MagicMock,
    ) -> None:
        """Test creating pipeline loads destination config if not provided."""
        mock_loader = MagicMock()
        mock_destination_config = MagicMock()
        mock_destination_config.type.value = "duckdb"
        mock_loader.load_destination_config.return_value = mock_destination_config
        mock_config_loader_class.return_value = mock_loader
        mock_pipeline_inst = MagicMock()
        mock_dlt_pipeline.return_value = mock_pipeline_inst

        mock_pipeline_config = MagicMock()
        mock_pipeline_config.source.config_file = "test_source.yaml"
        mock_pipeline_config.destination.config_file = "test_destination.yaml"
        mock_source_config = MagicMock()

        factory = PipelineFactory()
        factory.create_pipeline(
            mock_pipeline_config,
            source_config=mock_source_config,
            destination_config=None,  # Not provided
        )

        mock_loader.load_destination_config.assert_called_once_with("test_destination.yaml")

    @patch("ingestion.pipelines.factory.SourceFactory")
    @patch("ingestion.pipelines.factory.ConfigLoader")
    def test_create_source(
        self,
        mock_config_loader_class: MagicMock,
        mock_source_factory_class: MagicMock,
    ) -> None:
        """Test creating source from config."""
        mock_config_loader_class.return_value = MagicMock()
        mock_source_factory = MagicMock()
        mock_resource_1 = MagicMock()
        mock_resource_2 = MagicMock()
        mock_source_factory.create_resources.return_value = [mock_resource_1, mock_resource_2]
        mock_source_factory_class.return_value = mock_source_factory

        mock_source_config = MagicMock()
        mock_pipeline_config = MagicMock()
        mock_pipeline_config.source.resources = ["users"]
        mock_pipeline_config.source.params = {"key": "value"}

        factory = PipelineFactory()
        resources = list(factory.create_source(mock_source_config, mock_pipeline_config))

        mock_source_factory.create_resources.assert_called_once_with(
            mock_source_config,
            ["users"],
            {"key": "value"},
        )
        assert resources == [mock_resource_1, mock_resource_2]

    @patch("ingestion.pipelines.factory.ConfigLoader")
    def test_get_destination_name_databricks(
        self,
        mock_config_loader_class: MagicMock,
    ) -> None:
        """Test getting destination name for Databricks."""
        mock_config_loader_class.return_value = MagicMock()
        mock_destination_config = MagicMock()
        mock_destination_config.type.value = DestinationType.DATABRICKS.value

        result = PipelineFactory._get_destination_name(mock_destination_config)  # type: ignore[attr-defined]
        assert result == "databricks"

    @patch("ingestion.pipelines.factory.ConfigLoader")
    def test_get_destination_name_snowflake(
        self,
        mock_config_loader_class: MagicMock,
    ) -> None:
        """Test getting destination name for Snowflake."""
        mock_config_loader_class.return_value = MagicMock()
        mock_destination_config = MagicMock()
        mock_destination_config.type.value = DestinationType.SNOWFLAKE.value

        result = PipelineFactory._get_destination_name(mock_destination_config)  # type: ignore[attr-defined]
        assert result == "snowflake"

    @patch("ingestion.pipelines.factory.ConfigLoader")
    def test_get_destination_name_bigquery(
        self,
        mock_config_loader_class: MagicMock,
    ) -> None:
        """Test getting destination name for BigQuery."""
        mock_config_loader_class.return_value = MagicMock()
        mock_destination_config = MagicMock()
        mock_destination_config.type.value = DestinationType.BIGQUERY.value

        result = PipelineFactory._get_destination_name(mock_destination_config)  # type: ignore[attr-defined]
        assert result == "bigquery"

    @patch("ingestion.pipelines.factory.ConfigLoader")
    def test_get_destination_name_postgres(
        self,
        mock_config_loader_class: MagicMock,
    ) -> None:
        """Test getting destination name for Postgres."""
        mock_config_loader_class.return_value = MagicMock()
        mock_destination_config = MagicMock()
        mock_destination_config.type.value = DestinationType.POSTGRES.value

        result = PipelineFactory._get_destination_name(mock_destination_config)  # type: ignore[attr-defined]
        assert result == "postgres"

    @patch("ingestion.pipelines.factory.ConfigLoader")
    def test_get_destination_name_duckdb(
        self,
        mock_config_loader_class: MagicMock,
    ) -> None:
        """Test getting destination name for DuckDB."""
        mock_config_loader_class.return_value = MagicMock()
        mock_destination_config = MagicMock()
        mock_destination_config.type.value = DestinationType.DUCKDB.value

        result = PipelineFactory._get_destination_name(mock_destination_config)  # type: ignore[attr-defined]
        assert result == "duckdb"

    @patch("ingestion.pipelines.factory.dlt.pipeline")
    @patch("ingestion.pipelines.factory.ConfigLoader")
    def test_load_and_create_pipeline(
        self,
        mock_config_loader_class: MagicMock,
        mock_dlt_pipeline: MagicMock,
    ) -> None:
        """Test load_and_create_pipeline method."""
        mock_loader = MagicMock()
        mock_pipeline_config = MagicMock()
        mock_pipeline_config.source.config_file = "test_source.yaml"
        mock_pipeline_config.destination.config_file = "test_destination.yaml"
        mock_loader.load_pipeline_config.return_value = mock_pipeline_config
        mock_source_config = MagicMock()
        mock_loader.load_source_config.return_value = mock_source_config
        mock_destination_config = MagicMock()
        mock_destination_config.type.value = "duckdb"
        mock_loader.load_destination_config.return_value = mock_destination_config
        mock_config_loader_class.return_value = mock_loader
        mock_pipeline_inst = MagicMock()
        mock_dlt_pipeline.return_value = mock_pipeline_inst

        factory = PipelineFactory()
        result = factory.load_and_create_pipeline("test_pipeline")

        mock_loader.load_pipeline_config.assert_called_once_with("test_pipeline.yaml")
        mock_loader.load_source_config.assert_called_once_with("test_source.yaml")
        mock_loader.load_destination_config.assert_called_once_with("test_destination.yaml")
        assert result == mock_pipeline_inst

    @patch("ingestion.pipelines.factory.ConfigLoader")
    def test_get_destination_credentials_databricks(
        self,
        mock_config_loader_class: MagicMock,
    ) -> None:
        """Test getting credentials for Databricks destination."""
        mock_config_loader_class.return_value = MagicMock()
        mock_destination_config = MagicMock()
        mock_destination_config.type.value = "databricks"
        mock_destination_config.connection.server_hostname_secret_key = "hostname123"
        mock_destination_config.connection.http_path_secret_key = "/path/123"
        mock_destination_config.connection.access_token_secret_key = "token123"
        mock_destination_config.connection.catalog = "main"
        mock_destination_config.connection.schema = "default"

        factory = PipelineFactory()
        credentials = factory.get_destination_credentials(mock_destination_config)

        assert credentials["server_hostname"] == "hostname123"
        assert credentials["http_path"] == "/path/123"
        assert credentials["access_token"] == "token123"
        assert credentials["catalog"] == "main"
        assert credentials["schema"] == "default"

    @patch("ingestion.pipelines.factory.ConfigLoader")
    def test_get_destination_credentials_non_databricks(
        self,
        mock_config_loader_class: MagicMock,
    ) -> None:
        """Test getting credentials for non-Databricks destination returns empty dict."""
        mock_config_loader_class.return_value = MagicMock()
        mock_destination_config = MagicMock()
        mock_destination_config.type.value = "duckdb"

        factory = PipelineFactory()
        credentials = factory.get_destination_credentials(mock_destination_config)

        assert credentials == {}
