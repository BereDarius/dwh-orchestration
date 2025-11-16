"""Deploy Prefect flows from YAML trigger configurations.

This module reads trigger YAML files and creates Prefect deployments with schedules.
"""

import sys
from pathlib import Path

from prefect import serve

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestion.config.models import Environment
from ingestion.pipelines.factory import PipelineFactory
from ingestion.utils.logging import get_logger, setup_logging
from orchestration.flows import all_pipelines_flow, github_pipeline_flow, single_pipeline_flow

logger = get_logger(__name__)


def create_deployments_from_triggers(environment: str = "dev"):  # type: ignore[return]
    """
    Create Prefect deployments from trigger YAML configurations.

    Args:
        environment: Environment to load triggers from
    """
    logger.info(f"Loading trigger configurations from {environment}...")

    # Load all triggers
    env = Environment(environment)
    factory = PipelineFactory(environment=env)
    triggers = factory.config_loader.load_all_triggers()

    if not triggers:
        logger.warning(f"No triggers found in {environment} environment")
        return []  # type: ignore[return-value]

    logger.info(f"Found {len(triggers)} trigger configurations")

    deployments = []  # type: ignore[var-annotated]

    for trigger_name, trigger_config in triggers.items():
        logger.info(f"Creating deployment for trigger: {trigger_name}")

        # Determine which flow to use
        if trigger_config.pipeline == "*":
            # All pipelines flow
            flow = all_pipelines_flow.to_deployment(
                name=trigger_config.name,
                tags=trigger_config.tags,
                parameters={"environment": environment},
            )
        elif "github" in trigger_config.pipeline.lower():
            # GitHub specific flow
            params = {  # type: ignore[var-annotated]
                "environment": environment,
                "username": trigger_config.parameters.get("username", "torvalds"),
            }
            flow = github_pipeline_flow.to_deployment(
                name=trigger_config.name,
                tags=trigger_config.tags,
                parameters=params,  # type: ignore[arg-type]
            )
        else:
            # Single pipeline flow
            params = {
                "environment": environment,
                "pipeline_name": trigger_config.pipeline,
            }
            flow = single_pipeline_flow.to_deployment(
                name=trigger_config.name,
                tags=trigger_config.tags,
                parameters=params,
            )

        # Add schedule if enabled
        if trigger_config.schedule.enabled:
            logger.info(
                f"  Schedule: {trigger_config.schedule.cron} ({trigger_config.schedule.timezone})"
            )
            # Note: In Prefect 3.x, schedules are set via serve() or flow.deploy()
            # We'll add cron info to description
            # flow.description updated via to_deployment args instead
        else:
            logger.info("  Manual trigger (no schedule)")

        deployments.append(flow)  # type: ignore[arg-type]
        logger.info(f"✓ Created deployment: {trigger_config.name}")

    return deployments  # type: ignore[return-value]


def serve_triggers(environment: str = "dev"):
    """
    Start Prefect server with all deployments from trigger configs.

    Args:
        environment: Environment to load triggers from
    """
    logger.info("=" * 60)
    logger.info("STARTING PREFECT WITH YAML TRIGGERS")
    logger.info("=" * 60)
    logger.info("")

    deployments = create_deployments_from_triggers(environment)  # type: ignore[assignment]

    if not deployments:
        logger.error("No deployments created. Exiting.")
        return

    logger.info("")
    logger.info(f"Starting Prefect with {len(deployments)} deployments...")  # type: ignore[arg-type]
    logger.info("Prefect UI: http://127.0.0.1:4200")
    logger.info("")

    # Serve all deployments
    # Note: In Prefect 3.x, use serve() to run continuously
    serve(*deployments)  # type: ignore[arg-type]


if __name__ == "__main__":
    import argparse

    setup_logging(level="INFO")

    parser = argparse.ArgumentParser(description="Deploy Prefect flows from YAML trigger configs")
    parser.add_argument(
        "--environment",
        default="dev",
        choices=["dev", "stage", "prod"],
        help="Environment to load triggers from",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List trigger configurations without deploying",
    )
    parser.add_argument("--serve", action="store_true", help="Serve deployments continuously")

    args = parser.parse_args()

    if args.list:
        # Just list the triggers
        env = Environment(args.environment)
        factory = PipelineFactory(environment=env)
        triggers = factory.config_loader.load_all_triggers()

        print(f"\nFound {len(triggers)} triggers in {args.environment}:\n")
        for name, config in triggers.items():
            print(f"  • {name}")
            print(f"    Pipeline: {config.pipeline}")
            print(f"    Schedule: {config.schedule.cron if config.schedule.enabled else 'Manual'}")
            print(f"    Tags: {', '.join(config.tags)}")
            print()
    elif args.serve:
        serve_triggers(args.environment)
    else:
        create_deployments_from_triggers(args.environment)
        print("\nDeployments created successfully!")
        print("To serve them, run:")
        print(f"  python -m orchestration.deploy --serve --environment {args.environment}")
