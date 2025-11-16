# Data Ingestion Framework

A production-ready, configuration-driven data ingestion framework built on DLT (Data Load Tool) with multi-environment support (dev/stage/prod), comprehensive testing, and Airflow orchestration.

## 🎯 Features

- **Configuration-Driven**: Define sources, destinations, and pipelines in simple YAML files
- **Multi-Environment**: Separate configurations for dev, stage, and prod environments
- **Secrets Management**: Secure secrets resolution from environment variables & GitHub Secrets
- **Type-Safe**: Full Pydantic validation for all configurations
- **100% Test Coverage**: Comprehensive unit tests with pytest
- **Dynamic DAG Generation**: Airflow DAGs automatically generated from YAML configs
- **Incremental Loading**: Built-in support for CDC and timestamp-based incremental loads
- **Data Quality**: Integrated data quality checks with Great Expectations
- **VS Code Optimized**: Pre-configured workspace with auto-formatting and linting

## 📁 Project Structure

```
data-ingestion-framework/
├── config/                      # Configuration files
│   └── environments/            # Environment-specific configs
│       ├── dev/                 # Development environment
│       ├── stage/               # Staging environment
│       └── prod/                # Production environment
├── src/ingestion/               # Source code
│   ├── config/                  # Configuration management
│   ├── sources/                 # Source implementations
│   ├── destinations/            # Destination handlers
│   ├── pipelines/               # Pipeline engine
│   └── utils/                   # Utilities
├── airflow/                     # Airflow DAGs and plugins
├── tests/                       # Test suite (100% coverage)
├── docker/                      # Docker configs per environment
└── docs/                        # Documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Docker & Docker Compose (for Airflow)
- Git

### 1. Clone and Setup

```bash
# Clone the repository
cd /Users/beredarius/Desktop/IT/fun/data-warehouse

# Make setup script executable
chmod +x scripts/setup.sh

# Run setup
./scripts/setup.sh
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.dev.example .env

# Edit .env and add your credentials
nano .env
```

### 3. Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 4. Validate Configuration

```bash
# Run quick start verification (checks everything)
python quickstart.py

# Or validate individually
python scripts/validate_configs.py --env dev
python scripts/validate_secrets.py --env dev
```

### 5. Run Example Pipeline

```bash
# Run the YouTube API example
python examples/run_youtube_pipeline.py

# Or use the CLI
ingestion run --pipeline youtube_to_databricks --env dev
```

### 6. Open in VS Code (Recommended)

```bash
code data-ingestion-framework.code-workspace
```

**You'll get:**

- Auto-formatting on save
- YAML auto-completion with validation
- One-click testing and debugging
- Coverage visualization

See [VS Code Setup Guide](docs/vscode-setup.md) for details.

### 5. Run Your First Pipeline

```bash
# Run a pipeline locally
python -m ingestion.cli run --pipeline youtube_to_databricks --env dev

# Or using the VS Code debugger (F5)
```

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
