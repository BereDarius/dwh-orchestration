"""Main orchestration entry point - fully YAML-driven data warehouse orchestration.

This module provides a single command-line interface for running the entire
data warehouse orchestration system based solely on YAML configuration files.

No Python code is required from data engineers - everything is configured via YAML.

Usage:
    # Start orchestration (loads all triggers and runs scheduled jobs)
    python -m orchestration.main

    # List all configurations
    python -m orchestration.main --list

    # Validate all configurations
    python -m orchestration.main --validate

Environment:
    Set the ENVIRONMENT variable to control which environment to use:
    export ENVIRONMENT=dev|stage|prod
"""

import sys
from pathlib import Path

from prefect import flow, serve, task

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestion.config.environment import get_environment
from ingestion.config.models import JobConfig
from ingestion.pipelines.executor import PipelineExecutor
from ingestion.pipelines.factory import PipelineFactory
from ingestion.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@task(
    name="execute_pipeline",
    description="Execute a single pipeline",
    retries=3,
    retry_delay_seconds=60,
)
def execute_pipeline_task(pipeline_name: str, parameters: dict | None = None) -> dict:
    """
    Execute a single pipeline.

    Args:
        pipeline_name: Name of the pipeline to execute
        parameters: Optional runtime parameters

    Returns:
        Dict with execution results
    """
    try:
        environment = get_environment()
        factory = PipelineFactory(environment=environment)

        logger.info(f"Loading pipeline: {pipeline_name}")
        pipeline_config = factory.config_loader.load_pipeline_config(f"{pipeline_name}.yaml")

        # Merge parameters if provided
        if parameters:
            pipeline_config.source.params.update(parameters)

        executor = PipelineExecutor(pipeline_config, environment)
        result = executor.execute()

        logger.info(f"✓ Pipeline {pipeline_name} completed successfully")
        return {"status": "success", "pipeline": pipeline_name, "result": result}

    except Exception as e:
        logger.error(f"✗ Pipeline {pipeline_name} failed: {e}")
        raise


@flow(name="execute_job", description="Execute a job (batch of pipelines)")
def execute_job_flow(job_config: JobConfig, parameters: dict | None = None):
    """
    Execute a job - a batch of pipelines with dependencies.

    Args:
        job_config: Job configuration
        parameters: Optional runtime parameters to override

    Returns:
        Dict with execution results
    """
    logger.info("=" * 80)
    logger.info(f"STARTING JOB: {job_config.name}")
    logger.info(f"Description: {job_config.description or 'N/A'}")
    logger.info(f"Pipelines: {len(job_config.pipelines)}")
    logger.info(f"Mode: {job_config.execution.mode}")
    logger.info("=" * 80)

    results = []

    if job_config.execution.mode == "sequential":
        # Execute pipelines one by one in order
        for pipeline_ref in sorted(job_config.pipelines, key=lambda p: p.order):
            if not pipeline_ref.enabled:
                logger.info(f"Skipping disabled pipeline: {pipeline_ref.name}")
                continue

            try:
                params = {**(parameters or {}), **pipeline_ref.parameters}
                result = execute_pipeline_task(pipeline_ref.name, params)
                results.append(result)
            except Exception as e:
                logger.error(f"Pipeline {pipeline_ref.name} failed: {e}")
                if not pipeline_ref.continue_on_failure:
                    raise

    elif job_config.execution.mode == "parallel":
        # Execute all pipelines in parallel
        futures = []
        for pipeline_ref in job_config.pipelines:
            if not pipeline_ref.enabled:
                continue
            params = {**(parameters or {}), **pipeline_ref.parameters}
            future = execute_pipeline_task.submit(pipeline_ref.name, params)
            futures.append((pipeline_ref.name, future))

        # Wait for all to complete
        for name, future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Pipeline {name} failed: {e}")
                if not job_config.execution.continue_on_failure:
                    raise

    elif job_config.execution.mode == "dag":
        # Execute pipelines respecting dependencies (DAG order)
        executed = set()
        pending = list(job_config.pipelines)

        while pending:
            # Find pipelines with no pending dependencies
            ready = [
                p for p in pending if p.enabled and all(dep in executed for dep in p.depends_on)
            ]

            if not ready:
                remaining = [p.name for p in pending if p.enabled]
                raise ValueError(f"Circular dependency or missing pipeline: {remaining}")

            # Execute ready pipelines in parallel
            futures = []
            for pipeline_ref in ready:
                params = {**(parameters or {}), **pipeline_ref.parameters}
                future = execute_pipeline_task.submit(pipeline_ref.name, params)
                futures.append((pipeline_ref.name, pipeline_ref, future))

            # Wait for this batch to complete
            for name, pipeline_ref, future in futures:
                try:
                    result = future.result()
                    results.append(result)
                    executed.add(name)
                except Exception as e:
                    logger.error(f"Pipeline {name} failed: {e}")
                    if not pipeline_ref.continue_on_failure:
                        raise
                finally:
                    pending.remove(pipeline_ref)

    logger.info("=" * 80)
    logger.info(f"JOB COMPLETED: {job_config.name}")
    logger.info(f"Pipelines executed: {len(results)}")
    logger.info("=" * 80)

    return {"status": "success", "job": job_config.name, "results": results}


def create_deployments_from_yaml():
    """
    Automatically discover and create Prefect deployments from YAML configurations.

    This function:
    1. Loads all trigger configurations
    2. Loads referenced job configurations
    3. Creates Prefect deployments with schedules
    4. Returns list of deployments ready to serve
    """
    environment = get_environment()
    logger.info(f"Loading configurations for environment: {environment.value}")

    factory = PipelineFactory(environment=environment)

    # Load all triggers
    triggers = factory.config_loader.load_all_triggers()
    if not triggers:
        logger.warning("No triggers found")
        return []

    logger.info(f"Found {len(triggers)} triggers")

    # Load all jobs
    jobs = factory.config_loader.load_all_jobs()
    if not jobs:
        logger.warning("No jobs found")
        return []

    logger.info(f"Found {len(jobs)} jobs")

    deployments = []

    for trigger_name, trigger_config in triggers.items():
        if not trigger_config.enabled:
            logger.info(f"Skipping disabled trigger: {trigger_name}")
            continue

        # Get the referenced job
        job_file = trigger_config.job.replace(".yaml", "").replace("jobs/", "")
        job_config = jobs.get(job_file)

        if not job_config:
            logger.error(f"Job not found for trigger {trigger_name}: {trigger_config.job}")
            continue

        logger.info(f"Creating deployment: {trigger_name} -> {job_config.name}")

        # Create flow for this job (use default argument to capture job_config)
        def make_flow(config: JobConfig):
            @flow(name=f"job_{config.name}")
            def job_flow(params: dict | None = None):
                return execute_job_flow(config, params)

            return job_flow

        flow_instance = make_flow(job_config)

        # Create deployment
        deployment_kwargs = {
            "name": trigger_name,
            "tags": trigger_config.tags + job_config.tags,
            "parameters": trigger_config.parameters,
        }

        # Add schedule if it's a cron trigger
        if trigger_config.type == "cron" and trigger_config.schedule:
            from prefect.client.schemas.schedules import CronSchedule

            deployment_kwargs["schedule"] = CronSchedule(
                cron=trigger_config.schedule.cron,
                timezone=trigger_config.schedule.timezone,
            )
            logger.info(
                f"  Schedule: {trigger_config.schedule.cron} ({trigger_config.schedule.timezone})"
            )
        elif trigger_config.type == "manual":
            logger.info("  Manual trigger (no schedule)")
        else:
            logger.info(f"  Trigger type: {trigger_config.type}")

        deployment = flow_instance.to_deployment(**deployment_kwargs)
        deployments.append(deployment)

        logger.info(f"✓ Created deployment for: {trigger_name}")

    return deployments


def list_all_configs():
    """List all YAML configurations in the system."""
    environment = get_environment()
    factory = PipelineFactory(environment=environment)

    print(f"\n{'=' * 80}")
    print(f"YAML CONFIGURATIONS - Environment: {environment.value.upper()}")
    print(f"{'=' * 80}\n")

    # Sources
    sources = factory.config_loader.load_all_sources()
    print(f"📥 SOURCES ({len(sources)}):")
    for name, config in sources.items():
        print(f"  • {name} ({config.type.value})")
        print(f"    Resources: {len(config.resources)}")
    print()

    # Destinations
    destinations = factory.config_loader.load_all_destinations()
    print(f"📤 DESTINATIONS ({len(destinations)}):")
    for name, config in destinations.items():
        print(f"  • {name} ({config.type.value})")
    print()

    # Pipelines
    pipelines = factory.config_loader.load_all_pipelines()
    print(f"🔄 PIPELINES ({len(pipelines)}):")
    for name, config in pipelines.items():
        print(f"  • {name}")
        print(f"    Source: {config.source.config_file}")
        print(f"    Destination: {config.destination.config_file}")
    print()

    # Jobs
    jobs = factory.config_loader.load_all_jobs()
    print(f"📦 JOBS ({len(jobs)}):")
    for name, config in jobs.items():
        print(f"  • {name}")
        print(f"    Pipelines: {len(config.pipelines)}")
        print(f"    Mode: {config.execution.mode}")
        if config.dependencies:
            print(f"    Dependencies: {', '.join(config.dependencies)}")
    print()

    # Triggers
    triggers = factory.config_loader.load_all_triggers()
    print(f"⏰ TRIGGERS ({len(triggers)}):")
    for name, config in triggers.items():
        status = "✓ ENABLED" if config.enabled else "✗ DISABLED"
        print(f"  • {name} [{status}]")
        print(f"    Type: {config.type}")
        print(f"    Job: {config.job}")
        if config.type == "cron" and config.schedule:
            print(f"    Schedule: {config.schedule.cron}")
    print()


def validate_all_configs():
    """Validate all YAML configurations."""
    environment = get_environment()
    factory = PipelineFactory(environment=environment)

    print(f"\n{'=' * 80}")
    print(f"VALIDATING CONFIGURATIONS - Environment: {environment.value.upper()}")
    print(f"{'=' * 80}\n")

    errors = []

    # Validate sources
    try:
        sources = factory.config_loader.load_all_sources()
        print(f"✓ Sources: {len(sources)} validated")
    except Exception as e:
        errors.append(f"Sources validation failed: {e}")
        print(f"✗ Sources validation failed: {e}")

    # Validate destinations
    try:
        destinations = factory.config_loader.load_all_destinations()
        print(f"✓ Destinations: {len(destinations)} validated")
    except Exception as e:
        errors.append(f"Destinations validation failed: {e}")
        print(f"✗ Destinations validation failed: {e}")

    # Validate pipelines
    try:
        pipelines = factory.config_loader.load_all_pipelines()
        print(f"✓ Pipelines: {len(pipelines)} validated")
    except Exception as e:
        errors.append(f"Pipelines validation failed: {e}")
        print(f"✗ Pipelines validation failed: {e}")

    # Validate jobs
    try:
        jobs = factory.config_loader.load_all_jobs()
        print(f"✓ Jobs: {len(jobs)} validated")
    except Exception as e:
        errors.append(f"Jobs validation failed: {e}")
        print(f"✗ Jobs validation failed: {e}")

    # Validate triggers
    try:
        triggers = factory.config_loader.load_all_triggers()
        print(f"✓ Triggers: {len(triggers)} validated")
    except Exception as e:
        errors.append(f"Triggers validation failed: {e}")
        print(f"✗ Triggers validation failed: {e}")

    print()
    if errors:
        print(f"{'=' * 80}")
        print(f"VALIDATION FAILED - {len(errors)} error(s)")
        print(f"{'=' * 80}")
        for error in errors:
            print(f"  • {error}")
        return False
    else:
        print(f"{'=' * 80}")
        print("✓ ALL CONFIGURATIONS VALID")
        print(f"{'=' * 80}")
        return True


def main():
    """Main entry point for YAML-driven orchestration."""
    import argparse

    parser = argparse.ArgumentParser(
        description="YAML-driven data warehouse orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start orchestration with all triggers
  python -m orchestration.main

  # List all configurations
  python -m orchestration.main --list

  # Validate all configurations
  python -m orchestration.main --validate

Environment:
  Set ENVIRONMENT variable before running:
    export ENVIRONMENT=dev
    export ENVIRONMENT=stage
    export ENVIRONMENT=prod
        """,
    )

    parser.add_argument("--list", action="store_true", help="List all YAML configurations")
    parser.add_argument("--validate", action="store_true", help="Validate all YAML configurations")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    setup_logging(level=args.log_level)

    try:
        environment = get_environment()
        logger.info(f"Environment: {environment.value}")
    except ValueError as e:
        logger.error(str(e))
        print("\nERROR: ENVIRONMENT variable not set!")
        print("Set it before running:")
        print("  export ENVIRONMENT=dev")
        sys.exit(1)

    if args.list:
        list_all_configs()
    elif args.validate:
        if not validate_all_configs():
            sys.exit(1)
    else:
        # Start orchestration
        logger.info("=" * 80)
        logger.info("STARTING YAML-DRIVEN ORCHESTRATION")
        logger.info("=" * 80)
        logger.info("")

        deployments = create_deployments_from_yaml()

        if not deployments:
            logger.error("No deployments created. Check your YAML configurations.")
            sys.exit(1)

        logger.info(f"\n✓ Created {len(deployments)} deployments")
        logger.info("\nPrefect UI: http://127.0.0.1:4200")
        logger.info("\nStarting Prefect server...\n")

        # Serve all deployments (runs continuously)
        serve(*deployments)


if __name__ == "__main__":
    main()
