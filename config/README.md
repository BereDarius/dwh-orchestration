# Configuration Directory

This directory contains all configuration files for the data warehouse orchestration framework.

## Structure

```
config/
├── sources/          # Data source configurations
├── destinations/     # Data destination configurations
├── pipelines/        # Pipeline configurations
├── jobs/             # Job configurations (batches of pipelines)
├── triggers/         # Trigger configurations (scheduling)
└── secrets_mapping.yaml  # Secret key mappings
```

## Environment Management

**⚠️ Important Change:** Environments are now managed via the `ENVIRONMENT` environment variable, not through separate directory structures.

### Setting the Environment

Set the `ENVIRONMENT` variable before running any commands:

```bash
# Development
export ENVIRONMENT=dev

# Staging
export ENVIRONMENT=stage

# Production
export ENVIRONMENT=prod
```

### How It Works

1. **Single Configuration Files**: All environments share the same configuration files
2. **Environment Variable**: The `ENVIRONMENT` variable controls which environment you're working in
3. **Secret Resolution**: Secrets are resolved based on the current environment automatically
4. **No Duplication**: No need to maintain separate config files for each environment

### Example

```bash
# Run pipeline in development
export ENVIRONMENT=dev
python -m orchestration.flows --pipeline github_to_duckdb

# Run same pipeline in production
export ENVIRONMENT=prod
python -m orchestration.flows --pipeline github_to_duckdb
```

The same configuration files are used, but secrets and environment-specific settings are resolved based on the `ENVIRONMENT` variable.

## Configuration Files

### Sources (`sources/`)

Define data sources (APIs, databases, files, streams).

Example: `sources/github_api.yaml`

```yaml
source:
  name: github_api
  type: rest_api
  connection:
    base_url: "https://api.github.com"
    timeout: 30
  resources:
    - name: repos
      endpoint: "/users/{username}/repos"
```

### Destinations (`destinations/`)

Define data destinations (warehouses, databases, data lakes).

Example: `destinations/duckdb_local.yaml`

```yaml
destination:
  name: local_duckdb
  type: duckdb
  connection:
    database: "data/warehouse.duckdb"
```

### Pipelines (`pipelines/`)

Define data pipelines connecting sources to destinations.

Example: `pipelines/github_to_duckdb.yaml`

```yaml
pipeline:
  name: github_to_duckdb
  source:
    config_file: github_api.yaml
    resources: [repos, issues]
  destination:
    config_file: duckdb_local.yaml
    dataset_name: github_data
```

### Jobs (`jobs/`)

Define batches of pipelines with dependencies.

Example: `jobs/daily_ingestion.yaml`

```yaml
job:
  name: daily_ingestion
  pipelines:
    - name: github_to_duckdb
      order: 1
    - name: analytics_processing
      order: 2
      depends_on: [github_to_duckdb]
  execution:
    mode: dag
```

### Triggers (`triggers/`)

Define when and how jobs should be executed.

Example: `triggers/daily_at_2am.yaml`

```yaml
trigger:
  name: daily_ingestion_trigger
  type: cron
  job: daily_ingestion.yaml
  schedule:
    cron: "0 2 * * *"
    timezone: "UTC"
```

## Secrets Management

Secrets are stored in `secrets_mapping.yaml` and resolved based on the current environment.

Example:

```yaml
secrets:
  github_token_secret_key:
    dev: GITHUB_TOKEN_DEV
    stage: GITHUB_TOKEN_STAGE
    prod: GITHUB_TOKEN_PROD
```

When `ENVIRONMENT=prod`, the system automatically uses `GITHUB_TOKEN_PROD` from your environment variables.

## Migration from Old Structure

If you had the old environment-based structure (`config/environments/dev/`, `config/environments/stage/`, etc.):

1. **Configs are now flat**: All configs are in `config/{sources,destinations,pipelines,jobs,triggers}/`
2. **No environment field**: The `environment` field has been removed from all YAML files
3. **Set ENVIRONMENT variable**: Always set `ENVIRONMENT` before running commands
4. **One set of configs**: Maintain one set of configuration files, not separate copies per environment

### Before (Old Structure)

```
config/
  environments/
    dev/
      sources/
        github_api.yaml  # environment: dev
    prod/
      sources/
        github_api.yaml  # environment: prod (duplicate!)
```

### After (New Structure)

```
config/
  sources/
    github_api.yaml  # No environment field

# Use ENVIRONMENT variable
export ENVIRONMENT=dev   # or stage, or prod
```

## Validation

All configuration files are validated against JSON schemas in `.vscode/schemas/`.

The VS Code YAML extension provides:

- ✅ Real-time validation
- ✅ Autocomplete
- ✅ Inline documentation
- ✅ Error highlighting

## Best Practices

1. **Always set ENVIRONMENT**: Never run without setting the environment variable
2. **Use meaningful names**: Name configs clearly (e.g., `github_public_api.yaml` not `api1.yaml`)
3. **Document with comments**: Add comments explaining non-obvious configuration
4. **Use secrets for sensitive data**: Never hardcode passwords or tokens
5. **Tag your configs**: Use tags for organization and filtering
6. **Version control friendly**: Single set of configs makes git history cleaner

## Environment-Specific Configuration

If you need environment-specific settings, use secret resolution:

```yaml
# Configuration file (same for all environments)
source:
  name: api
  connection:
    url_secret_key: api_url_secret_key # Resolved per environment
    timeout: 30

# secrets_mapping.yaml
secrets:
  api_url_secret_key:
    dev: API_URL_DEV # http://localhost:8000
    stage: API_URL_STAGE # https://stage-api.example.com
    prod: API_URL_PROD # https://api.example.com
```

This way, the same config file works across all environments with appropriate values.
