# Configuration Schemas

This directory contains JSON schemas for validating YAML configuration files used throughout the data warehouse orchestration framework.

## Schema Files

### 1. Source Schema (`source-schema.json`)

Validates data source configurations with type-specific validation.

**Supported Source Types:**

- `rest_api` - REST API data sources with authentication
- `database` - Database connections (SQL queries or table extracts)
- `file` - File-based sources (CSV, JSON, Parquet, etc.)
- `stream` - Streaming data sources

**Features:**

- Conditional validation based on source type
- Secret key validation patterns
- Retry and timeout configurations
- Resource-level configuration (endpoints, queries, etc.)

**Example:** `config/sources/github_api.yaml`

---

### 2. Destination Schema (`destination-schema.json`)

Validates data destination configurations with extensive type-specific settings.

**Supported Destination Types:**

- `databricks`, `snowflake`, `bigquery`, `postgres`, `duckdb`
- `mssql`, `azuresynapse`, `clickhouse`, `redshift`, `athena`
- `delta`, `iceberg`, `filesystem`
- `weaviate`, `lancedb`, `qdrant`, `dremio`, `motherduck`

**Features:**

- Comprehensive conditional validation per destination type
- Connection parameters with secret key support
- Destination-specific settings (naming conventions, staging, optimization)
- Retry and timeout policies

**Example:** `config/destinations/local_duckdb.yaml`

---

### 3. Pipeline Schema (`pipeline-schema.json`)

Validates data pipeline configurations that connect sources to destinations.

**Required Fields:**

- `name` - Unique pipeline identifier
- `environment` - Environment (dev/stage/prod)
- `source` - Source configuration reference
- `destination` - Destination configuration reference

**Features:**

- Pipeline dependencies (run after other pipelines complete)
- Source and destination configuration file references
- Resource selection and parameter overrides
- Execution settings (retries, timeout)
- Monitoring and alerting configuration
- Tags for organization

**Example:** `config/pipelines/github_to_duckdb.yaml`

---

### 4. Job Schema (`job-schema.json`) ⭐ **NEW**

Validates job configurations - batches of pipelines with dependencies.

**Key Concepts:**

- **Job**: A collection of pipelines executed together
- **Pipeline Dependencies**: Pipelines within a job can depend on each other
- **Job Dependencies**: Jobs can depend on other jobs completing first

**Required Fields:**

- `name` - Unique job identifier
- `environment` - Environment (dev/stage/prod)
- `pipelines` - Array of pipeline configurations

**Execution Modes:**

- `sequential` - Run pipelines one by one in order
- `parallel` - Run all pipelines simultaneously
- `dag` - Respect dependencies (Directed Acyclic Graph)

**Features:**

- Inter-pipeline dependencies within a job
- Inter-job dependencies across jobs
- Execution order control
- Per-pipeline parameter overrides
- Retry configuration with exponential backoff
- Notifications (email, Slack, PagerDuty, webhook)
- SLA monitoring
- Metadata (owner, version, documentation)

**Example:** `config/jobs/daily_data_ingestion.yaml`

---

### 5. Trigger Schema (`trigger-schema.json`) ⭐ **NEW**

Validates trigger configurations - defines when and how jobs are executed.

**Trigger Types:**

- `cron` - Schedule-based triggers (cron expressions)
- `interval` - Time interval triggers (every N minutes/hours/days)
- `manual` - Manual execution via API or UI
- `event` - Event-driven triggers (S3, Kafka, SNS, etc.)
- `webhook` - HTTP webhook triggers from external systems

**Features:**

- Type-specific validation (cron requires schedule, webhook requires path, etc.)
- Timezone support
- Catchup for missed schedules
- Jitter for preventing thundering herd
- Event filtering and payload mapping
- Webhook authentication (token, HMAC, OAuth2)
- Parameter passing to jobs

**Examples:**

- `config/triggers/daily_ingestion.yaml` (cron)
- `config/triggers/realtime_monitoring.yaml` (interval)
- `config/triggers/manual_backfill.yaml` (manual)
- `config/triggers/webhook_refresh.yaml` (webhook)

---

## Architecture

```
Trigger → Job → Pipeline(s) → Source + Destination
```

### Data Flow Example

```yaml
# 1. Trigger (WHEN to run)
trigger:
  type: cron
  schedule:
    cron: "0 2 * * *" # Daily at 2 AM
  job: daily_data_ingestion.yaml

# 2. Job (WHAT to run)
job:
  name: daily_data_ingestion
  dependencies:
    - prerequisite_job # Wait for this job first
  pipelines:
    - name: github_to_duckdb
      order: 1
      depends_on: [] # No dependencies

    - name: analytics_processing
      order: 2
      depends_on:
        - github_to_duckdb # Wait for GitHub pipeline

# 3. Pipeline (HOW to move data)
pipeline:
  name: github_to_duckdb
  source:
    config_file: github_api.yaml
    resources: [repos, issues]
  destination:
    config_file: local_duckdb.yaml
    dataset_name: github_data
```

---

## Dependencies

### Job Dependencies

Jobs can depend on other jobs completing successfully:

```yaml
job:
  name: reporting_job
  dependencies:
    - data_ingestion_job # Must complete first
    - data_quality_job # Must complete first
  pipelines:
    - name: generate_reports
```

**Execution:** `reporting_job` only runs after both `data_ingestion_job` and `data_quality_job` succeed.

### Pipeline Dependencies (within a Job)

Pipelines within a job can depend on each other:

```yaml
job:
  name: etl_job
  execution:
    mode: dag # Respect dependencies
  pipelines:
    - name: extract_raw_data
      order: 1
      depends_on: []

    - name: transform_data
      order: 2
      depends_on:
        - extract_raw_data # Wait for extraction

    - name: load_to_warehouse
      order: 3
      depends_on:
        - transform_data # Wait for transformation
```

**Execution:** Pipelines run in dependency order automatically when `mode: dag`.

---

## VS Code Integration

The schemas are automatically applied to YAML files through `.vscode/settings.json`:

```json
{
  "yaml.schemas": {
    ".vscode/schemas/source-schema.json": "config/**/sources/*.yaml",
    ".vscode/schemas/destination-schema.json": "config/**/destinations/*.yaml",
    ".vscode/schemas/pipeline-schema.json": "config/**/pipelines/*.yaml",
    ".vscode/schemas/trigger-schema.json": "config/**/triggers/*.yaml",
    ".vscode/schemas/job-schema.json": "config/**/jobs/*.yaml"
  }
}
```

**Benefits:**

- ✅ Real-time validation while editing
- ✅ IntelliSense autocomplete
- ✅ Inline documentation
- ✅ Error highlighting
- ✅ Type-specific field suggestions

---

## Validation Rules

### Secret Keys

All secret references must end with `_secret_key`:

```yaml
connection:
  password_secret_key: "my_password_secret_key" # ✅ Valid
  password: "hardcoded_password" # ❌ Invalid
```

### Naming Conventions

Names must be lowercase with underscores:

```yaml
job:
  name: my_job_name      # ✅ Valid
  name: MyJobName        # ❌ Invalid (uppercase)
  name: my-job-name      # ❌ Invalid (hyphens)
```

### Cron Expressions

Must be valid cron format:

```yaml
schedule:
  cron: "0 * * * *"      # ✅ Every hour
  cron: "0 2 * * *"      # ✅ Daily at 2 AM
  cron: "@hourly"        # ✅ Shorthand
  cron: "invalid"        # ❌ Invalid format
```

### Dependencies

Pipeline dependencies must reference pipelines within the same job:

```yaml
job:
  pipelines:
    - name: pipeline_a
      depends_on:
        - pipeline_b # ✅ Valid (pipeline_b is in this job)
        - other_job_pipeline # ❌ Invalid (not in this job)
```

---

## Best Practices

1. **Use Tags**: Organize configurations with meaningful tags

   ```yaml
   tags: [production, critical, hourly]
   ```

2. **Set SLAs**: Define expected completion times

   ```yaml
   sla:
     max_duration_minutes: 30
     expected_completion_time: "09:00"
   ```

3. **Enable Notifications**: Configure alerts for failures

   ```yaml
   notifications:
     on_failure: true
     channels: [slack, email]
   ```

4. **Document Ownership**: Add metadata for accountability

   ```yaml
   metadata:
     owner: "data-team"
     runbook_url: "https://runbooks.example.com/job"
   ```

5. **Use DAG Mode**: Let the system handle dependencies automatically

   ```yaml
   execution:
     mode: dag
   ```

6. **Add Jitter**: Prevent thundering herd with random delays

   ```yaml
   schedule:
     jitter: 60 # Up to 60 seconds
   ```

7. **Configure Retries**: Handle transient failures gracefully
   ```yaml
   retries:
     max_attempts: 3
     exponential_backoff: true
     retry_on: [timeout, connection_error]
   ```

---

## Schema Validation

To validate your configuration files manually:

```bash
# Install YAML validator
pip install pyyaml jsonschema

# Validate a job
python -m jsonschema -i config/jobs/my_job.yaml .vscode/schemas/job-schema.json

# Validate a trigger
python -m jsonschema -i config/triggers/my_trigger.yaml .vscode/schemas/trigger-schema.json
```

Or use the VS Code YAML extension which validates automatically!

---

## Examples

See the example configurations in:

- `config/jobs/` - Job examples
- `config/triggers/` - Trigger examples
- `config/pipelines/` - Pipeline examples
- `config/sources/` - Source examples
- `config/environments/dev/destinations/` - Destination examples

---

## Migration Guide

### From Old Trigger System to New Job/Trigger System

**Old System (Direct Pipeline Triggers):**

```yaml
trigger:
  pipeline: github_to_duckdb
  schedule:
    cron: "0 * * * *"
```

**New System (Job-based Triggers):**

```yaml
# 1. Create a job
# config/environments/dev/jobs/github_job.yaml
job:
  name: github_job
  pipelines:
    - name: github_to_duckdb

# 2. Create a trigger for the job
# config/environments/dev/triggers/github_trigger.yaml
trigger:
  type: cron
  job: github_job.yaml
  schedule:
    cron: "0 * * * *"
```

**Benefits:**

- Run multiple pipelines together
- Add dependencies between pipelines
- Better monitoring and error handling
- Reuse jobs across multiple triggers
