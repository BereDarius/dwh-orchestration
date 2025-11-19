# Data Ingestion Framework

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
│   ├── sources/                 # Data source definitions
│   ├── destinations/            # Data warehouse/lake destinations
│   ├── pipelines/               # ETL pipeline definitions
│   ├── jobs/                    # Job definitions (batches of pipelines)
│   ├── triggers/                # Scheduling and trigger definitions
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
# Clone and navigate to project
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

### 4. Edit Configurations (YAML Only)

Open VS Code and edit YAML files in `config/`:

```bash
code data-ingestion-framework.code-workspace
```

**You'll get:**

- Real-time YAML validation
- Auto-completion for all fields
- Inline documentation
- Instant error detection

See [Config README](config/README.md) for detailed configuration guide.

## 📝 Configuration Guide

### Defining a Source

Create a YAML file in `config/environments/{env}/sources/`:

```yaml
source:
  name: my_api
  type: rest_api
  environment: dev

  connection:
    base_url: "https://api.example.com"
    auth:
      type: bearer
      credentials_secret_key: "API_TOKEN_DEV"
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

### Defining a Destination

Create a YAML file in `config/environments/{env}/destinations/`:

```yaml
destination:
  name: databricks_dev
  type: databricks
  environment: dev

  connection:
    server_hostname_secret_key: "DATABRICKS_HOST_DEV"
    http_path_secret_key: "DATABRICKS_HTTP_PATH_DEV"
    access_token_secret_key: "DATABRICKS_TOKEN_DEV"
    catalog: "dev_catalog"
    schema: "raw_data"

  settings:
    table_format: "delta"
    optimize_after_write: true
```

### Defining a Pipeline

Create a YAML file in `config/environments/{env}/pipelines/`:

```yaml
pipeline:
  name: my_pipeline
  environment: dev

  source:
    config_file: "sources/my_api.yaml"
    resources:
      - users

  destination:
    config_file: "destinations/databricks.yaml"
    dataset_name: "my_dataset"

  schedule:
    enabled: true
    cron: "0 */6 * * *" # Every 6 hours
```

**Dynamic Discovery**: Once you save the YAML file, it's automatically discovered by the framework. No code changes needed!

```bash
# Your new pipeline will appear here
ingestion list-pipelines --env dev

# And can be run immediately
ingestion run --pipeline my_pipeline --env dev
```

destination:
config_file: "destinations/databricks.yaml"
dataset_name: "my_dataset"

schedule:
enabled: true
cron: "0 _/6 _ \* \*" # Every 6 hours

````

## 🧪 Testing

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/unit/test_config_loader.py

# Generate coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
````

**Note**: The project requires **100% test coverage**. Tests will fail if coverage drops below this threshold.

## 🎮 Using the Framework

### CLI Commands

```bash
# List available pipelines
ingestion list-pipelines --env dev

# List all sources
ingestion list-sources --env dev

# List all destinations
ingestion list-destinations --env dev

# Discover all configurations
ingestion discover --env dev

# Validate a pipeline
ingestion validate --pipeline youtube_to_databricks --env dev

# Check secrets
ingestion check-secrets --env dev

# Run a pipeline
ingestion run --pipeline youtube_to_databricks --env dev

# Run with custom log level
ingestion --log-level DEBUG run --pipeline youtube_to_databricks
```

### Using Scripts

```bash
# List all configurations (detailed view)
python scripts/list_configs.py --env dev

# Validate all configurations
python scripts/validate_configs.py --env dev

# Check all required secrets
python scripts/validate_secrets.py --env dev
```

### Programmatic Usage

```python
from ingestion.config import ConfigLoader
from ingestion.config.models import Environment
from ingestion.pipelines import PipelineExecutor

# Initialize loader for dev environment
loader = ConfigLoader(Environment.DEV)

# Discover all configurations dynamically
all_configs = loader.discover_all_configs()
print(f"Found {len(all_configs['pipelines'])} pipelines")

# Load specific pipeline
pipeline_config = loader.load_pipeline_config("youtube_to_databricks.yaml")

# Execute pipeline
executor = PipelineExecutor()
result = executor.execute_pipeline_with_retry("youtube_to_databricks")

if result.success:
    print(f"Completed in {result.duration_seconds}s")
    print(f"Processed {result.rows_processed} rows")

# Or work with all pipelines dynamically
pipelines = loader.load_all_pipelines()
for name, config in pipelines.items():
    if config.schedule.enabled:
        result = executor.execute_pipeline(name)
        print(f"{name}: {'✓' if result.success else '✗'}")
```

### Examples

See the `examples/` directory for complete examples:

```bash
# Run the YouTube API example
python examples/run_youtube_pipeline.py
```

## 🐳 Docker & Airflow

### Start Airflow

```bash
# Switch to dev environment
./scripts/switch_env.sh dev

# Start Airflow
cd docker/dev
docker-compose up -d

# Access Airflow UI
open http://localhost:8080
```

### Deploy to Stage/Prod

Deployments to stage and prod are automated via GitHub Actions.

## 🔐 Secrets Management

Secrets are managed through:

1. **Local Development**: `.env` file
2. **CI/CD**: GitHub Secrets

### Adding a Secret

1. Add to `config/environments/{env}/secrets_mapping.yaml`:

```yaml
secrets:
  MY_SECRET_KEY:
    github_secret: "MY_SECRET_KEY"
    description: "Description of the secret"
    required: true
```

2. Add to `.env.{env}.example`:

```bash
MY_SECRET_KEY=placeholder-value
```

3. For GitHub Actions, add to repository secrets

## 📊 Monitoring

The framework includes built-in monitoring:

- Pipeline execution metrics
- Data quality scores
- Error tracking (with Sentry in prod)
- Custom alerts via email/Slack

## 🛠️ Development

### VS Code Setup

The project includes a fully configured VS Code workspace with:

**Automatic Features:**

- ✨ **Auto-formatting** with Black on save (100 char line length)
- 📦 **Auto-import sorting** with isort on save
- 🔍 **Real-time linting** with Ruff
- 🎯 **Type checking** with Pylance (strict mode)
- 📊 **Coverage gutters** showing test coverage inline
- ✅ **YAML validation** with JSON schemas for all config files

**Open the workspace:**

```bash
code data-ingestion-framework.code-workspace
```

**Install recommended extensions** when prompted (13 extensions):

- Python, Pylance, Black, Ruff, isort
- YAML, Docker, GitLens
- Error Lens, Coverage Gutters, Todo Tree
- Better Comments, Path Intellisense

**YAML Auto-completion:**
When editing YAML config files, you get:

- IntelliSense with field suggestions
- Validation against JSON schemas
- Hover documentation for all fields
- Error highlighting for invalid values

### Running Tasks

Use VS Code tasks (Cmd+Shift+P → "Tasks: Run Task"):

**Testing:**

- `Run Tests` - Run pytest
- `Run Tests with Coverage` - With coverage report (default)

**Code Quality:**

- `Format Code` - Run Black + isort
- `Lint Code` - Run Ruff
- `Type Check` - Run mypy

**Configuration:**

- `Validate Configs` - Validate all YAML configs
- `List All Configs` - Show detailed config listing
- `Discover Configs (CLI)` - Run discovery command
- `Switch Environment` - Switch between dev/stage/prod

**Setup:**

- `Setup Project` - Run initial setup script
- `Run Quickstart` - Verify installation

### Debug Configurations

Press F5 or use the Debug panel to run:

**Execution:**

- `Python: Current File` - Debug any Python file
- `Run Pipeline (Dev)` - Debug YouTube pipeline
- `List Pipelines` - Debug pipeline listing
- `Discover All Configs` - Debug config discovery

**Testing:**

- `Run Tests with Coverage` - Debug all tests
- `Run Current Test File` - Debug open test file

All debug configs include proper PYTHONPATH and environment variables.

## 📚 Documentation

Detailed documentation is available in the `docs/` directory:

- [Getting Started](docs/getting-started.md)
- [Configuration Guide](docs/configuration-guide.md)
- [API Sources](docs/source-setup/api-sources.md)
- [Database Sources](docs/source-setup/database-sources.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Ensure tests pass with 100% coverage
4. Run pre-commit hooks
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file

## 👥 Support

For questions or issues:

- Open a GitHub issue
- Contact: data-engineering@example.com

## 🗺️ Roadmap

- [ ] Add support for more source types (PostgreSQL, MySQL, S3)
- [ ] Add support for more destinations (Snowflake, BigQuery)
- [ ] Implement transformation layer
- [ ] Add data lineage tracking
- [ ] Add web UI for pipeline monitoring
