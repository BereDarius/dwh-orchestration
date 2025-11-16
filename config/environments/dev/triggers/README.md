# YAML-Based Pipeline Triggers

Configure pipeline schedules and execution using YAML files instead of code.

## Quick Start

### 1. View Configured Triggers

```bash
python -m orchestration.deploy --list
```

### 2. Run with YAML Triggers

```bash
# Start Prefect server first
./scripts/start_prefect.sh

# In another terminal, deploy from YAML configs
python -m orchestration.deploy --serve
```

## Trigger Configuration Format

Create YAML files in `config/environments/{env}/triggers/`:

```yaml
trigger:
  name: my_pipeline_trigger
  description: "Description of what this trigger does"

  # Pipeline to execute
  pipeline: "pipeline_name" # or "*" for all pipelines

  # Schedule (optional)
  schedule:
    enabled: true
    cron: "0 2 * * *" # Daily at 2 AM UTC
    timezone: "UTC"

  # Pipeline parameters (optional)
  parameters:
    key: "value"

  # Execution settings (for multi-pipeline triggers)
  execution:
    parallel: true
    continue_on_failure: false

  # Retry configuration
  retries:
    max_attempts: 3
    retry_delay_seconds: 60

  # Tags for organization
  tags:
    - tag1
    - tag2
```

## Example Triggers

### Hourly Pipeline

`config/environments/dev/triggers/github_hourly.yaml`:

```yaml
trigger:
  name: github_hourly
  description: "Fetch GitHub data every hour"
  pipeline: github_to_duckdb

  schedule:
    enabled: true
    cron: "0 * * * *"
    timezone: "UTC"

  parameters:
    username: "torvalds"

  retries:
    max_attempts: 3
    retry_delay_seconds: 60

  tags:
    - github
    - hourly
```

### Daily Batch (All Pipelines)

`config/environments/dev/triggers/all_pipelines_daily.yaml`:

```yaml
trigger:
  name: all_pipelines_daily
  description: "Run all pipelines once per day"
  pipeline: "*" # Wildcard for all pipelines

  schedule:
    enabled: true
    cron: "0 2 * * *"
    timezone: "UTC"

  execution:
    parallel: true
    continue_on_failure: true

  tags:
    - daily
    - batch
```

### Manual Trigger (No Schedule)

`config/environments/dev/triggers/manual_pipeline.yaml`:

```yaml
trigger:
  name: manual_pipeline
  description: "Manual execution only"
  pipeline: my_pipeline

  schedule:
    enabled: false # No automatic schedule

  tags:
    - manual
```

## Cron Schedule Examples

```yaml
# Every minute
cron: "* * * * *"

# Every hour at minute 0
cron: "0 * * * *"

# Every day at 2:00 AM
cron: "0 2 * * *"

# Every Monday at 9:00 AM
cron: "0 9 * * 1"

# First day of month at midnight
cron: "0 0 1 * *"

# Every 6 hours
cron: "0 */6 * * *"

# Weekdays at 8:00 AM
cron: "0 8 * * 1-5"
```

See [crontab.guru](https://crontab.guru/) for more examples.

## Commands

### List Triggers

```bash
# List triggers for dev environment
python -m orchestration.deploy --list

# List triggers for production
python -m orchestration.deploy --list --environment prod
```

### Deploy and Serve

```bash
# Serve deployments from triggers (starts continuously)
python -m orchestration.deploy --serve

# Serve production triggers
python -m orchestration.deploy --serve --environment prod
```

## Benefits of YAML Triggers

✅ **Configuration as Code** - Version control your schedules
✅ **Environment-Specific** - Different schedules per environment
✅ **No Code Changes** - Update schedules without touching Python
✅ **Easy Testing** - Quick enable/disable with `enabled: false`
✅ **Clear Documentation** - Self-documenting trigger configurations
✅ **Team Collaboration** - Non-developers can adjust schedules

## Directory Structure

```
config/
└── environments/
    ├── dev/
    │   └── triggers/
    │       ├── github_hourly.yaml
    │       ├── all_pipelines_daily.yaml
    │       └── mock_manual.yaml
    ├── stage/
    │   └── triggers/
    │       └── production_test_daily.yaml
    └── prod/
        └── triggers/
            ├── critical_hourly.yaml
            └── batch_nightly.yaml
```

## Integration with Prefect

Triggers are converted to Prefect deployments automatically:

1. **Schedule enabled** → Creates scheduled deployment
2. **Schedule disabled** → Creates manual deployment
3. **Pipeline: "\*"** → Uses `all_pipelines_flow`
4. **Pipeline: "name"** → Uses `single_pipeline_flow`
5. **Tags** → Applied to deployment for filtering

## Validation

Trigger configs are validated using Pydantic models:

- `TriggerConfig` - Main trigger configuration
- `TriggerScheduleConfig` - Schedule settings
- `TriggerExecutionConfig` - Execution behavior
- `TriggerRetryConfig` - Retry configuration

Invalid configs will raise validation errors with clear messages.

## Migration from Code

**Before (in Python):**

```python
deployment = flow.to_deployment(
    name="github-hourly",
    schedule=CronSchedule(cron="0 * * * *"),
    parameters={"username": "torvalds"},
)
```

**After (YAML):**

```yaml
trigger:
  name: github_hourly
  pipeline: github_to_duckdb
  schedule:
    enabled: true
    cron: "0 * * * *"
  parameters:
    username: "torvalds"
```

## Best Practices

1. **Descriptive Names** - Use clear trigger names like `github_hourly` not `trigger1`
2. **Add Descriptions** - Document what each trigger does
3. **Use Tags** - Organize triggers with tags (environment, frequency, team)
4. **Test First** - Use manual triggers (`enabled: false`) to test before scheduling
5. **Environment Separation** - Different schedules for dev/stage/prod
6. **Monitor Failures** - Set appropriate retry attempts for reliability

## Troubleshooting

### Trigger not appearing

- Check YAML syntax with a validator
- Ensure file is in correct directory: `config/environments/{env}/triggers/`
- File must end with `.yaml` extension
- Run `--list` to see if it's loaded

### Schedule not working

- Verify `enabled: true` in schedule section
- Check cron syntax at [crontab.guru](https://crontab.guru/)
- Ensure Prefect server is running
- Check Prefect UI for deployment status

### Wrong pipeline executing

- Verify `pipeline:` matches exact pipeline config filename (without .yaml)
- For all pipelines, use `pipeline: "*"`
- Check parameters are being passed correctly
