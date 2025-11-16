"""Pipeline executor for running DLT pipelines."""

import time
from datetime import datetime
from typing import Any

from dlt.common.pipeline import LoadInfo

from ingestion.config.models import PipelineConfig, SourceConfig
from ingestion.pipelines.factory import PipelineFactory
from ingestion.utils.logging import get_logger

logger = get_logger(__name__)


class PipelineExecutionResult:
    """Result of a pipeline execution."""

    def __init__(
        self,
        pipeline_name: str,
        success: bool,
        load_info: LoadInfo | None = None,
        error: Exception | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize execution result.

        Args:
            pipeline_name: Name of the pipeline
            success: Whether execution was successful
            load_info: DLT load information
            error: Exception if execution failed
            start_time: When execution started
            end_time: When execution ended
            metrics: Execution metrics
        """
        self.pipeline_name = pipeline_name
        self.success = success
        self.load_info = load_info
        self.error = error
        self.start_time = start_time or datetime.now()
        self.end_time = end_time or datetime.now()
        self.metrics = metrics or {}

    @property
    def duration_seconds(self) -> float:
        """Get execution duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    @property
    def rows_processed(self) -> int:
        """Get number of rows processed."""
        if self.load_info and hasattr(self.load_info, "row_counts"):
            return sum(self.load_info.row_counts.values())  # type: ignore[attr-defined]
        return 0

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "pipeline_name": self.pipeline_name,
            "success": self.success,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "rows_processed": self.rows_processed,
            "error": str(self.error) if self.error else None,
            "metrics": self.metrics,
        }


class PipelineExecutor:
    """Executes DLT pipelines based on configuration."""

    def __init__(self, pipeline_factory: PipelineFactory | None = None) -> None:
        """
        Initialize pipeline executor.

        Args:
            pipeline_factory: Pipeline factory (will create new one if not provided)
        """
        self.pipeline_factory = pipeline_factory or PipelineFactory()

    def execute_pipeline(
        self,
        pipeline_name: str,
        pipeline_config: PipelineConfig | None = None,
        source_config: SourceConfig | None = None,
    ) -> PipelineExecutionResult:
        """
        Execute a pipeline.

        Args:
            pipeline_name: Name of the pipeline to execute
            pipeline_config: Optional pipeline config (will be loaded if not provided)
            source_config: Optional source config (will be loaded if not provided)

        Returns:
            Pipeline execution result
        """
        start_time = datetime.now()
        logger.info(f"Starting pipeline execution: {pipeline_name}")

        try:
            # Load configs if not provided
            if pipeline_config is None:
                pipeline_config = self.pipeline_factory.config_loader.load_pipeline_config(
                    f"{pipeline_name}.yaml"
                )

            if source_config is None:
                source_config = self.pipeline_factory.config_loader.load_source_config(
                    pipeline_config.source.config_file
                )

            # Create pipeline
            pipeline = self.pipeline_factory.create_pipeline(pipeline_config)

            # Create source
            source = self.pipeline_factory.create_source(source_config, pipeline_config)

            # Run pipeline
            logger.info(f"Running pipeline: {pipeline_name}")
            load_info = pipeline.run(source)

            end_time = datetime.now()

            # Log success
            logger.info(
                f"Pipeline {pipeline_name} completed successfully. "
                f"Duration: {(end_time - start_time).total_seconds():.2f}s"
            )

            return PipelineExecutionResult(
                pipeline_name=pipeline_name,
                success=True,
                load_info=load_info,
                start_time=start_time,
                end_time=end_time,
                metrics=self._extract_metrics(load_info),
            )

        except Exception as e:
            end_time = datetime.now()
            logger.error(
                f"Pipeline {pipeline_name} failed: {str(e)}",
                exc_info=True,
            )

            return PipelineExecutionResult(
                pipeline_name=pipeline_name,
                success=False,
                error=e,
                start_time=start_time,
                end_time=end_time,
            )

    def execute_pipeline_with_retry(
        self,
        pipeline_name: str,
        max_retries: int | None = None,
        retry_delay: int | None = None,
    ) -> PipelineExecutionResult:
        """
        Execute pipeline with retry logic.

        Args:
            pipeline_name: Name of the pipeline to execute
            max_retries: Maximum number of retries (from config if not provided)
            retry_delay: Delay between retries in seconds (from config if not provided)

        Returns:
            Pipeline execution result
        """
        # Load pipeline config to get retry settings
        pipeline_config = self.pipeline_factory.config_loader.load_pipeline_config(
            f"{pipeline_name}.yaml"
        )

        max_retries = max_retries or pipeline_config.execution.retries
        retry_delay = retry_delay or pipeline_config.execution.retry_delay

        last_result = None

        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"Retrying pipeline {pipeline_name} (attempt {attempt}/{max_retries})")
                time.sleep(retry_delay)

            result = self.execute_pipeline(pipeline_name, pipeline_config)

            if result.success:
                return result

            last_result = result

        # All attempts failed
        assert last_result is not None
        logger.error(f"Pipeline {pipeline_name} failed after {max_retries + 1} attempts")
        return last_result

    @staticmethod
    def _extract_metrics(load_info: LoadInfo) -> dict[str, Any]:
        """
        Extract metrics from load info.

        Args:
            load_info: DLT load information

        Returns:
            Dictionary of metrics
        """
        metrics: dict[str, Any] = {}

        if hasattr(load_info, "row_counts"):
            metrics["row_counts"] = dict(load_info.row_counts)  # type: ignore[attr-defined]
            metrics["total_rows"] = sum(load_info.row_counts.values())  # type: ignore[attr-defined]

        if hasattr(load_info, "load_id"):
            metrics["load_id"] = load_info.load_id  # type: ignore[attr-defined]

        if hasattr(load_info, "destination_name"):
            metrics["destination"] = load_info.destination_name

        return metrics
