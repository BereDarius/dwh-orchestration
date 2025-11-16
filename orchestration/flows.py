"""Prefect flows for orchestrating data ingestion pipelines.

This module wraps the existing pipeline executor with Prefect flows to enable:
- Scheduled pipeline execution
- Parallel pipeline runs
- Retry logic and error handling
- Monitoring and observability
- Deployment management

Usage:
    # Run a single pipeline
    python -m orchestration.flows --pipeline github_to_duckdb

    # Run all pipelines
    python -m orchestration.flows --all

    # Deploy flows for scheduling
    python -m orchestration.flows --deploy
"""

import sys
from pathlib import Path
from typing import Any

from prefect import flow, task

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestion.config.models import Environment, PipelineConfig
from ingestion.pipelines.executor import PipelineExecutor
from ingestion.pipelines.factory import PipelineFactory
from ingestion.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@task(
    name="execute_pipeline_task",
    description="Execute a single data ingestion pipeline",
    retries=3,
    retry_delay_seconds=60,
    tags=["ingestion", "pipeline"],
)
def execute_pipeline_task(
    pipeline_name: str,
    environment: str = "dev",
    pipeline_config: PipelineConfig | None = None,
) -> dict[str, Any]:
    """
    Execute a data ingestion pipeline.

    Args:
        pipeline_name: Name of the pipeline to execute
        environment: Environment (dev/stage/prod)
        pipeline_config: Optional pipeline config override

    Returns:
        Dictionary with execution results
    """
    logger.info(f"Executing pipeline: {pipeline_name} in {environment}")

    # Create factory and executor
    env = Environment(environment)
    factory = PipelineFactory(environment=env)
    executor = PipelineExecutor(pipeline_factory=factory)

    # Execute pipeline
    result = executor.execute_pipeline(pipeline_name=pipeline_name, pipeline_config=pipeline_config)

    # Convert result to dict for Prefect state tracking
    result_dict = result.to_dict()

    if result.success:
        logger.info(
            f"Pipeline {pipeline_name} succeeded: {result.rows_processed} rows in {result.duration_seconds:.2f}s"
        )
    else:
        logger.error(f"Pipeline {pipeline_name} failed: {result.error}")
        raise Exception(f"Pipeline execution failed: {result.error}")

    return result_dict


@flow(
    name="single_pipeline_flow",
    description="Execute a single data ingestion pipeline",
    log_prints=True,
)
def single_pipeline_flow(
    pipeline_name: str,
    environment: str = "dev",
) -> dict[str, Any]:
    """
    Flow to execute a single pipeline.

    Args:
        pipeline_name: Name of the pipeline to execute
        environment: Environment (dev/stage/prod)

    Returns:
        Execution result dictionary
    """
    logger.info(f"Starting single pipeline flow: {pipeline_name}")
    result = execute_pipeline_task(pipeline_name=pipeline_name, environment=environment)
    logger.info(f"Completed single pipeline flow: {pipeline_name}")
    return result


@flow(
    name="all_pipelines_flow",
    description="Execute all configured pipelines in parallel",
    log_prints=True,
)
def all_pipelines_flow(
    environment: str = "dev",
    pipeline_names: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Flow to execute multiple pipelines in parallel.

    Args:
        environment: Environment (dev/stage/prod)
        pipeline_names: Optional list of pipeline names (auto-discover if None)

    Returns:
        Dictionary of pipeline results keyed by pipeline name
    """
    logger.info(f"Starting all pipelines flow in {environment}")

    # Auto-discover pipelines if not specified
    if pipeline_names is None:
        env = Environment(environment)
        factory = PipelineFactory(environment=env)
        # List all pipeline YAML files in the environment's pipelines directory
        pipelines_dir = factory.config_loader.config_path / "pipelines"
        pipeline_files = list(pipelines_dir.glob("*.yaml"))
        pipeline_names = [f.stem for f in pipeline_files]
        logger.info(f"Auto-discovered {len(pipeline_names)} pipelines")

    # Execute all pipelines in parallel
    results = {}
    futures = []

    for pipeline_name in pipeline_names:
        future = execute_pipeline_task.submit(pipeline_name=pipeline_name, environment=environment)  # type: ignore[call-overload]
        futures.append((pipeline_name, future))  # type: ignore[arg-type]

    # Collect results
    for pipeline_name, future in futures:  # type: ignore[misc]
        try:
            result = future.result()  # type: ignore[attr-defined]
            results[pipeline_name] = result
            logger.info(f"Pipeline {pipeline_name} completed successfully")
        except Exception as e:
            logger.error(f"Pipeline {pipeline_name} failed: {e}")
            results[pipeline_name] = {
                "success": False,
                "error": str(e),
                "pipeline_name": pipeline_name,
            }

    succeeded = len([r for r in results.values() if r.get("success")])  # type: ignore[union-attr]
    failed = len([r for r in results.values() if not r.get("success")])  # type: ignore[union-attr]
    logger.info(f"Completed all pipelines flow: {succeeded} succeeded, {failed} failed")

    return results  # type: ignore[return-value]


@flow(
    name="github_pipeline_flow",
    description="Execute GitHub API pipeline",
    log_prints=True,
)
def github_pipeline_flow(
    username: str = "torvalds",
    environment: str = "dev",
) -> dict[str, Any]:
    """
    Flow specifically for GitHub pipeline with custom parameters.

    Args:
        username: GitHub username to fetch repos from
        environment: Environment (dev/stage/prod)

    Returns:
        Execution result dictionary
    """
    logger.info(f"Starting GitHub pipeline flow for user: {username}")

    # Load pipeline config and override username
    env = Environment(environment)
    factory = PipelineFactory(environment=env)
    pipeline_config = factory.config_loader.load_pipeline_config("github_to_duckdb.yaml")
    pipeline_config.source.params["username"] = username

    # Execute
    result = execute_pipeline_task(
        pipeline_name="github_to_duckdb",
        environment=environment,
        pipeline_config=pipeline_config,
    )

    logger.info(f"Completed GitHub pipeline flow for user: {username}")
    return result


def create_deployments():
    """Create Prefect deployments using flow.serve() for Prefect 3.x."""
    logger.info("Creating Prefect deployments...")
    logger.info("")
    logger.info("To deploy flows with schedules in Prefect 3.x, use one of these methods:")
    logger.info("")
    logger.info("1. Deploy with CLI (recommended):")
    logger.info("   Create a prefect.yaml file and run:")
    logger.info("   prefect deploy")
    logger.info("")
    logger.info("2. Serve flows programmatically:")
    logger.info("   Use flow.serve() in the code to run continuously")
    logger.info("")
    logger.info("3. Use prefect.yaml for deployments:")
    logger.info("   Run: prefect init")
    logger.info("   Then: prefect deploy --all")
    logger.info("")
    logger.info("For now, run flows directly without deployment:")
    logger.info("  python -m orchestration.flows --github-user torvalds")
    logger.info("  python -m orchestration.flows --all")


if __name__ == "__main__":
    import argparse

    setup_logging(level="INFO")

    parser = argparse.ArgumentParser(description="Run Prefect data ingestion flows")
    parser.add_argument("--pipeline", help="Run a specific pipeline", default=None, type=str)
    parser.add_argument("--all", help="Run all pipelines", action="store_true", default=False)
    parser.add_argument(
        "--github-user",
        help="Run GitHub pipeline for specific user",
        default=None,
        type=str,
    )
    parser.add_argument(
        "--environment",
        help="Environment (dev/stage/prod)",
        default="dev",
        choices=["dev", "stage", "prod"],
    )
    parser.add_argument("--deploy", help="Create Prefect deployments", action="store_true")

    args = parser.parse_args()

    if args.deploy:
        create_deployments()
    elif args.pipeline:
        single_pipeline_flow(pipeline_name=args.pipeline, environment=args.environment)
    elif args.all:
        all_pipelines_flow(environment=args.environment)
    elif args.github_user:
        github_pipeline_flow(username=args.github_user, environment=args.environment)
    else:
        parser.print_help()
        print("\n")
        print("Examples:")
        print("  # Run GitHub pipeline")
        print("  python -m orchestration.flows --github-user torvalds")
        print("")
        print("  # Run all pipelines")
        print("  python -m orchestration.flows --all")
        print("")
        print("  # Run specific pipeline")
        print("  python -m orchestration.flows --pipeline mock_to_duckdb")
        print("")
        print("  # Create deployments for scheduling")
        print("  python -m orchestration.flows --deploy")
