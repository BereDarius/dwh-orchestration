# Prefect Orchestration Configuration

This directory contains Prefect flows for orchestrating data ingestion pipelines.

## Quick Start

### 1. Start Prefect Server

```bash
./scripts/start_prefect.sh
```

The Prefect UI will be available at http://127.0.0.1:4200

### 2. Deploy Flows (in another terminal)

```bash
source venv/bin/activate
python -m orchestration.flows --deploy
```

This creates three deployments:

- **single-pipeline-manual** - Manual trigger for any pipeline
- **all-pipelines-daily** - Runs all pipelines daily at 2 AM UTC
- **github-pipeline-hourly** - Fetches GitHub data every hour

### 3. Start a Worker

```bash
source venv/bin/activate
prefect worker start --pool default
```

## Manual Flow Execution

Run flows without the server:

```bash
# Run GitHub pipeline for a specific user
python -m orchestration.flows --github-user torvalds

# Run all configured pipelines
python -m orchestration.flows --all

# Run a specific pipeline
python -m orchestration.flows --pipeline github_to_duckdb --environment dev
```

## Available Flows

### `single_pipeline_flow`

Execute any single pipeline by name.

**Parameters:**

- `pipeline_name` (str): Name of the pipeline (e.g., "github_to_duckdb")
- `environment` (str): Environment - dev/stage/prod (default: "dev")

**Usage:**

```bash
python -m orchestration.flows --pipeline mock_to_duckdb
```

### `all_pipelines_flow`

Execute all configured pipelines in parallel.

**Parameters:**

- `environment` (str): Environment - dev/stage/prod (default: "dev")
- `pipeline_names` (list[str], optional): Specific pipelines to run (auto-discovers if None)

**Usage:**

```bash
python -m orchestration.flows --all --environment dev
```

### `github_pipeline_flow`

Execute GitHub pipeline with custom username parameter.

**Parameters:**

- `username` (str): GitHub username (default: "torvalds")
- `environment` (str): Environment - dev/stage/prod (default: "dev")

**Usage:**

```bash
python -m orchestration.flows --github-user python
```

## Prefect UI Features

Once the server is running, visit http://127.0.0.1:4200 to:

- **View flow runs** - See real-time execution status
- **Trigger deployments** - Manually run scheduled flows
- **Monitor logs** - View detailed execution logs
- **Track metrics** - See rows processed, duration, success/failure
- **Manage schedules** - Adjust cron schedules
- **View artifacts** - Inspect pipeline results

## Deployment Schedules

### All Pipelines - Daily

- **Schedule:** Daily at 2:00 AM UTC
- **Cron:** `0 2 * * *`
- **Purpose:** Full refresh of all data sources

### GitHub Pipeline - Hourly

- **Schedule:** Every hour on the hour
- **Cron:** `0 * * * *`
- **Purpose:** Keep repository data fresh

## Modifying Schedules

Edit `orchestration/flows.py` and update the `CronSchedule` in `create_deployments()`:

```python
schedule=CronSchedule(cron="0 */6 * * *", timezone="UTC")  # Every 6 hours
```

Then redeploy:

```bash
python -m orchestration.flows --deploy
```

## Retry Configuration

Pipelines automatically retry on failure:

- **Max retries:** 3
- **Retry delay:** 60 seconds
- **Exponential backoff:** Managed by Prefect

Customize in the `@task` decorator:

```python
@task(
    retries=5,
    retry_delay_seconds=120,
)
```

## Parallel Execution

The `all_pipelines_flow` executes pipelines in parallel using Prefect's task concurrency.

To control parallelism, set task runner:

```python
@flow(task_runner=DaskTaskRunner())
def all_pipelines_flow(...):
    ...
```

## Monitoring & Alerts

### View in UI

- Flow runs: http://127.0.0.1:4200/flow-runs
- Logs: Click any flow run for detailed logs

### CLI Monitoring

```bash
# Watch flow runs
prefect flow-run ls --limit 10

# View specific run logs
prefect flow-run logs <flow-run-id>
```

## Production Deployment

For production, use:

1. **Prefect Cloud** (recommended)

   - Managed service with full features
   - Sign up at https://app.prefect.cloud

2. **Self-hosted Server**

   - Deploy with Docker
   - Configure PostgreSQL backend
   - Set up worker pools

3. **GitHub Actions / Airflow**
   - Run flows via CI/CD
   - Keep using Prefect for local dev

## Architecture

```
orchestration/
├── __init__.py
├── flows.py          # Prefect flow definitions
└── README.md         # This file

Flow Execution:
┌─────────────┐
│ Prefect     │
│ Scheduler   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Flow        │ ─── Wraps existing framework
│ (Task)      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Pipeline    │
│ Executor    │ ─── Your existing code
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ DLT + Data  │
│ Sources     │
└─────────────┘
```

## Troubleshooting

### Server won't start

```bash
# Reset database
prefect server database reset -y

# Start with debug logging
prefect server start --log-level DEBUG
```

### Deployments not showing

```bash
# List deployments
prefect deployment ls

# Rebuild deployment
python -m orchestration.flows --deploy
```

### Worker not picking up runs

```bash
# Check worker pools
prefect work-pool ls

# Start worker with debug
prefect worker start --pool default --log-level DEBUG
```

## Next Steps

1. **Add more flows** - Create custom flows for specific use cases
2. **Configure notifications** - Set up Slack/email alerts on failure
3. **Add data quality checks** - Integrate Great Expectations results
4. **Scale with Dask** - Use DaskTaskRunner for large datasets
5. **Deploy to production** - Use Prefect Cloud or self-hosted server
