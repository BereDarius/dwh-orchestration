# Prefect Orchestration - Updated for Prefect 3.x

This directory contains Prefect 3.x flows for orchestrating data ingestion pipelines.

## Quick Start (3 Steps)

### 1. Start Prefect Server
\`\`\`bash
source venv/bin/activate
prefect config set PREFECT_API_URL="http://127.0.0.1:4200/api"
prefect server start --host 127.0.0.1
\`\`\`
UI available at: **http://127.0.0.1:4200**

### 2. Run a Flow
\`\`\`bash
# In another terminal
source venv/bin/activate
python -m orchestration.flows --github-user torvalds
\`\`\`

### 3. View in UI
Open http://127.0.0.1:4200/runs to see your flow execution!

## Available Commands

\`\`\`bash
# GitHub pipeline with custom user
python -m orchestration.flows --github-user python

# Run all pipelines in parallel
python -m orchestration.flows --all

# Run specific pipeline
python -m orchestration.flows --pipeline mock_to_duckdb
\`\`\`

## Prefect 3.x Changes

**Old way (Prefect 2.x):**
\`\`\`python
# Deployment.build_from_flow() - REMOVED in 3.x
deployment = Deployment.build_from_flow(...)
\`\`\`

**New way (Prefect 3.x):**
\`\`\`bash
# Option 1: prefect.yaml (recommended)
prefect init
prefect deploy --all

# Option 2: flow.serve()
flow.serve(name="my-flow", cron="0 * * * *")

# Option 3: flow.deploy()
flow.deploy(name="my-flow", cron="0 * * * *")
\`\`\`

## Scheduling Deployments

### Using prefect.yaml
\`\`\`yaml
deployments:
  - name: github-hourly
    entrypoint: orchestration/flows.py:github_pipeline_flow
    schedule:
      cron: "0 * * * *"
      timezone: "UTC"
    parameters:
      username: "torvalds"
\`\`\`

Then: `prefect deploy --all`

## Features

✅ **Auto-tracking** - All runs appear in UI automatically  
✅ **Parallel execution** - Multiple pipelines run concurrently  
✅ **Retry logic** - 3 attempts, 60s delay  
✅ **Real-time logs** - Stream logs in UI  
✅ **Metrics** - Rows processed, duration, success/failure  

## Troubleshooting

\`\`\`bash
# Server not starting
prefect config set PREFECT_API_URL="http://127.0.0.1:4200/api"

# Check server status
curl http://127.0.0.1:4200/api/health

# View configuration
prefect config view
\`\`\`

## Production

- **Prefect Cloud**: https://app.prefect.cloud (managed)
- **Self-hosted**: Docker + PostgreSQL backend
- **Hybrid**: Cloud UI + local workers

See full documentation in the original README or Prefect docs.
