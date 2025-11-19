# Data Warehouse Orchestration Framework

A production-ready, **100% YAML-driven** data orchestration framework where data engineers never write Python code. Define everything through YAML configurations: sources, destinations, pipelines, jobs, and triggers. The framework automatically handles orchestration, dependencies, scheduling, and execution.

## 🎯 Key Philosophy

**Zero Python Required for Data Engineers**

- Data engineers work exclusively with YAML configuration files
- Framework automatically discovers and orchestrates all configs
- Dependencies resolved automatically (job-level and pipeline-level)
- Scheduling handled through trigger definitions
- Built on Prefect for robust orchestration

## ✨ Features

- **100% YAML-Driven**: No Python code needed - pure YAML configuration
- **Auto-Discovery**: Automatically finds and loads all YAML configs
- **Smart Dependencies**: DAG execution with automatic dependency resolution
- **Multi-Environment**: Single config set, environment controlled via `ENVIRONMENT` variable
- **Secure Secrets**: Automatic secret resolution from environment variables
- **Type-Safe**: Full Pydantic validation for all configurations
- **Real-time Validation**: VS Code integration with JSON schemas for instant feedback
- **Flexible Scheduling**: Cron, interval, manual, event, and webhook triggers
- **Job Orchestration**: Batch pipelines with sequential, parallel, or DAG execution modes

## 📁 Project Structure

```
data-warehouse/
├── config/                      # YAML configuration files (data engineers work here)
│   ├── sources/                 # Data source definitions (3 files)
│   ├── destinations/            # Data warehouse/lake destinations (2 files)
│   ├── pipelines/               # ETL pipeline definitions (3 files)
│   ├── jobs/                    # Job definitions - batches of pipelines (3 files)
│   ├── triggers/                # Scheduling and trigger definitions (7 files)
│   └── secrets_mapping.yaml     # Secret key mappings
├── orchestration/               # Orchestration engine (no changes needed)
│   └── main.py                  # Single entry point for everything
├── src/ingestion/               # Framework code (no changes needed)
│   ├── config/                  # Configuration management
│   ├── sources/                 # Source implementations
│   ├── destinations/            # Destination handlers
│   └── pipelines/               # Pipeline engine
├── tests/                       # Test suite
└── .vscode/schemas/             # JSON schemas for YAML validation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Virtual environment with dependencies installed

### 1. Setup Environment

```bash
# Navigate to project
cd data-warehouse

# Activate virtual environment
source venv/bin/activate

# Set environment (dev/stage/prod)
export ENVIRONMENT=dev
```

### 2. Validate Configurations

```bash
# Validate all YAML configs
python -m orchestration.main --validate

# List all configurations
python -m orchestration.main --list
```

### 3. Start Orchestration

```bash
# Start the orchestration system (runs continuously)
python -m orchestration.main
```

This will:
- Auto-discover all YAML configurations
- Create Prefect flows for all jobs
- Set up all triggers and schedules
- Start the Prefect server
- Run scheduled pipelines automatically

**Prefect UI**: http://127.0.0.1:4200

## 📝 YAML Configuration Guide

All configuration is done through YAML files in the `config/` directory. See [config/README.md](config/README.md) for comprehensive documentation.

### 1. Define a Source

Create `config/sources/my_api.yaml`:

```yaml
source:
  name: my_api
  type: rest_api

  connection:
    base_url: "https://api.example.com"
    auth:
      type: bearer
      credentials_secret_key: "my_api_token_secret_key"
    timeout: 30
    retry:
      max_attempts: 3
      backoff_factor: 2

  resources:
    - name: users
      endpoint: "/users"
      incremental:
        enabled: true
        cursor_field: "updated_at"
        initial_value: "2024-01-01T00:00:00Z"
      primary_key: ["id"]
      write_disposition: "merge"
```

### 2. Define a Destination

Create `config/destinations/my_warehouse.yaml`:

```yaml
destination:
  name: my_warehouse
  type: duckdb

  connection:
    database: "./my_data.duckdb"

  settings:
    schema: "raw_data"
    create_indexes: true
```

### 3. Define a Pipeline

Create `config/pipelines/my_pipeline.yaml`:

```yaml
pipeline:
  name: my_pipeline
  description: "Ingest users from API to warehouse"

  source:
    config_file: "my_api.yaml"
    resources:
      - users

  destination:
    config_file: "my_warehouse.yaml"
    dataset_name: "my_dataset"

  retry:
    max_attempts: 3
    initial_delay: 60
```

### 4. Define a Job (Batch of Pipelines)

Create `config/jobs/daily_ingestion.yaml`:

```yaml
job:
  name: daily_ingestion
  description: "Daily data ingestion from all sources"

  pipelines:
    - name: my_pipeline
      order: 1
      enabled: true

  execution:
    mode: sequential  # or: parallel, dag
    max_parallelism: 3
    continue_on_failure: false

  retries:
    max_attempts: 2
    retry_delay: 300
    exponential_backoff: true

  notifications:
    on_failure: true
    on_success: false
    channels: ["email"]

  sla:
    duration: 3600  # 1 hour
```

### 5. Define a Trigger (Schedule)

Create `config/triggers/daily_schedule.yaml`:

```yaml
trigger:
  name: daily_schedule
  type: cron
  enabled: true
  job: daily_ingestion.yaml

  schedule:
    cron: "0 2 * * *"  # Run at 2 AM daily
    timezone: "UTC"
    catchup: false

  tags:
    - daily
    - production
```

### 6. Run It!

```bash
# Validate all configs
python -m orchestration.main --validate

# List everything
python -m orchestration.main --list

# Start orchestration (trigger will run at scheduled time)
python -m orchestration.main
```

**That's it!** No Python code needed. The framework automatically:
- ✅ Discovers all YAML configs
- ✅ Resolves dependencies
- ✅ Creates execution graph
- ✅ Schedules jobs via triggers
- ✅ Handles retries and failures
- ✅ Sends notifications

## 🔄 Orchestration Commands

### Main Entry Point

```bash
# Start orchestration (runs continuously with all schedules)
python -m orchestration.main

# List all configurations
python -m orchestration.main --list

# Validate all configurations
python -m orchestration.main --validate

# Custom log level
python -m orchestration.main --log-level DEBUG
```

**Output Example:**

```
================================================================================
YAML CONFIGURATIONS - Environment: DEV
================================================================================

📥 SOURCES (3):
  • github_api (rest_api)
    Resources: 3
  • mock_api (rest_api)
    Resources: 1
  • youtube_api (rest_api)
    Resources: 2

📤 DESTINATIONS (2):
  • duckdb_local (duckdb)
  • databricks (databricks)

🔄 PIPELINES (3):
  • github_to_duckdb
    Source: github_api.yaml
    Destination: duckdb_local.yaml
  • mock_to_duckdb
    Source: mock_api.yaml
    Destination: duckdb_local.yaml
  • youtube_to_databricks
    Source: youtube_api.yaml
    Destination: databricks.yaml

📦 JOBS (3):
  • all_pipelines_job
    Pipelines: 3
    Mode: parallel
  • hourly_analytics
    Pipelines: 1
    Mode: sequential
  • mock_pipeline_job
    Pipelines: 1
    Mode: sequential

⏰ TRIGGERS (7):
  • daily_ingestion [✓ ENABLED]
    Type: cron
    Job: all_pipelines_job.yaml
    Schedule: 0 1 * * *
  • github_hourly [✓ ENABLED]
    Type: cron
    Job: hourly_analytics.yaml
    Schedule: 0 * * * *
  • manual_backfill [✓ ENABLED]
    Type: manual
    Job: all_pipelines_job.yaml
```

### Environment Management

```bash
# Set environment
export ENVIRONMENT=dev    # or stage, prod

# Verify current environment
python -c "from ingestion.config.environment import get_environment; print(get_environment())"
```

### Utility Scripts

```bash
# List all configurations (detailed view)
python scripts/list_configs.py

# Validate all configurations
python scripts/validate_configs.py

# Check all required secrets
python scripts/validate_secrets.py
```

## 🔐 Secrets Management

Secrets are resolved automatically from environment variables based on `config/secrets_mapping.yaml`.

### Adding a New Secret

1. **Add to secrets mapping** (`config/secrets_mapping.yaml`):

```yaml
secrets:
  my_api_token:
    env_var_dev: "MY_API_TOKEN_DEV"
    env_var_stage: "MY_API_TOKEN_STAGE"
    env_var_prod: "MY_API_TOKEN_PROD"
    description: "API authentication token"
    required: true
```

2. **Reference in YAML config**:

```yaml
source:
  connection:
    auth:
      credentials_secret_key: "my_api_token_secret_key"
```

3. **Set environment variable**:

```bash
export MY_API_TOKEN_DEV="your-token-here"
```

The framework automatically:
- Uses correct environment variable based on `ENVIRONMENT`
- Validates required secrets are present
- Resolves secrets at runtime

## 🎨 VS Code Setup

For the best development experience, use VS Code with the provided workspace configuration.

### Open Workspace

```bash
code data-ingestion-framework.code-workspace
```

### Features

**Automatic:**
- ✨ **Real-time YAML validation** - Invalid configs highlighted instantly
- 📝 **Auto-completion** - IntelliSense for all YAML fields
- 📖 **Inline documentation** - Hover to see field descriptions
- ❌ **Error highlighting** - See validation errors as you type
- 🔍 **Schema validation** - All configs validated against JSON schemas

**When editing YAML files:**
- Type-ahead suggestions for all fields
- Validation against type-specific schemas
- Documentation on hover
- Enum value suggestions

### Install Recommended Extensions

When opening the workspace, VS Code will prompt to install 13 recommended extensions. Click "Install All" for:

- Python, Pylance, Black, Ruff, isort
- YAML, Docker, GitLens
- Error Lens, Coverage Gutters, Todo Tree
- Better Comments, Path Intellisense

## 🧪 Testing

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/unit/test_config_loader.py

# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

**VS Code Tasks:**

- `Run Tests` - Quick test run
- `Run Tests with Coverage` - Full coverage report (default)
- `Format Code` - Black + isort
- `Lint Code` - Ruff checks
- `Type Check` - mypy validation

Access via: `Cmd+Shift+P` → "Tasks: Run Task"

## 📚 Configuration Deep Dive

See [config/README.md](config/README.md) for:

- Complete field reference for all YAML types
- Environment variable patterns
- Secret resolution details
- Dependency configuration
- Advanced examples
- Best practices

## 🏗️ Architecture

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        YAML Configs                             │
│  (data engineers edit these - no Python needed)                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ Auto-Discovery
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   orchestration/main.py                         │
│  - Loads all YAMLs from config/                                 │
│  - Validates against JSON schemas                               │
│  - Builds dependency graph                                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ Dynamic Flow Generation
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Prefect Flows                              │
│  - One flow per job                                             │
│  - Respects dependencies                                        │
│  - Handles retries, notifications, SLAs                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ Trigger-based Execution
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Pipeline Execution                           │
│  - Runs based on trigger schedules                              │
│  - Sequential/Parallel/DAG modes                                │
│  - Automatic secret resolution                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Execution Modes

**Sequential**: Pipelines run one after another in `order`

**Parallel**: All pipelines run simultaneously (up to `max_parallelism`)

**DAG**: Respects `depends_on` relationships, runs in parallel where possible

## 🛠️ Development Workflow

### For Data Engineers (YAML Only)

1. Edit YAML files in `config/` using VS Code
2. Save (validation happens automatically)
3. Run `python -m orchestration.main --validate`
4. Run `python -m orchestration.main` to test
5. Commit YAML changes to git

**No Python code changes needed!**

### For Framework Developers (Python)

1. Make changes to `src/ingestion/` or `orchestration/`
2. Run tests: `pytest --cov=src`
3. Format: `black src tests && isort src tests`
4. Lint: `ruff check src tests`
5. Type check: `mypy src`
6. Commit changes

## 🐳 Deployment

### Local Development

```bash
export ENVIRONMENT=dev
python -m orchestration.main
```

### Production (Systemd)

See [deployment/README.md](deployment/README.md) for:
- Systemd service configuration
- Docker deployment
- Environment setup
- Monitoring setup

## 📊 Monitoring

Access the Prefect UI to monitor:
- Flow runs and status
- Execution duration
- Failure logs
- Scheduled triggers

**Prefect UI**: http://127.0.0.1:4200

## 🤝 Contributing

1. Create a feature branch
2. Make your changes (YAML for configs, Python for framework)
3. Ensure tests pass: `pytest --cov=src`
4. Run pre-commit hooks: `pre-commit run --all-files`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file

## 🗺️ Roadmap

- [x] YAML-driven configuration
- [x] Auto-discovery and orchestration
- [x] Job and trigger system
- [x] Multiple execution modes
- [ ] Web UI for configuration
- [ ] Data lineage tracking
- [ ] Advanced transformations
- [ ] More source/destination types
