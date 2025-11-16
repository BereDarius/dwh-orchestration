# Examples

This directory contains example scripts demonstrating how to use the Data Ingestion Framework.

## Available Examples

### 1. Dynamic Discovery (`dynamic_discovery.py`)

Demonstrates how the framework automatically discovers all YAML configurations:

- Discovers all sources, destinations, and pipelines
- Shows detailed information about each configuration
- Demonstrates that no code changes are needed to add new configs

**Usage:**

```bash
python examples/dynamic_discovery.py
```

**What it shows:**

- Automatic discovery of all config files
- Listing all available sources and destinations
- Detailed pipeline information
- How to add new configurations dynamically

### 2. YouTube API Pipeline (`run_youtube_pipeline.py`)

Demonstrates the complete workflow:

- Loading YAML configurations
- Validating configurations and secrets
- Executing a pipeline
- Handling results

**Usage:**

```bash
# Set environment variables
export ENVIRONMENT=dev
export YOUTUBE_API_KEY_DEV=your_api_key_here
export DATABRICKS_SERVER_HOSTNAME_DEV=your_hostname
export DATABRICKS_HTTP_PATH_DEV=your_http_path
export DATABRICKS_ACCESS_TOKEN_DEV=your_token

# Run the example
python examples/run_youtube_pipeline.py
```

**What it does:**

1. Loads configuration from `config/environments/dev/`
2. Validates all configurations
3. Checks that required secrets are available
4. Displays configuration summary
5. (Optional) Executes the pipeline

## Using the CLI

You can also use the CLI tool to explore configurations dynamically:

```bash
# Discover all configurations
ingestion discover --env dev

# List available pipelines
ingestion list-pipelines --env dev

# List all sources
ingestion list-sources --env dev

# List all destinations
ingestion list-destinations --env dev

# Validate a pipeline
ingestion validate --pipeline youtube_to_databricks --env dev

# Check secrets
ingestion check-secrets --env dev

# Run a pipeline
ingestion run --pipeline youtube_to_databricks --env dev
```

## Creating Your Own Pipeline

To create a new pipeline (dynamically discovered):

1. Create configuration files in `config/environments/{env}/`:

   - `sources/my_source.yaml` - Define your data source
   - `destinations/my_destination.yaml` - Define your destination
   - `pipelines/my_pipeline.yaml` - Connect source to destination

2. Add required secrets to your `.env.{env}` file

3. **That's it!** The framework will automatically discover your new configs:

   ```bash
   # Your new pipeline appears automatically
   ingestion list-pipelines --env dev

   # Run it immediately
   ingestion run --pipeline my_pipeline --env dev
   ```

No code changes needed - everything is loaded dynamically from YAML files!

- `sources/my_source.yaml` - Define your data source
- `destinations/my_destination.yaml` - Define your destination
- `pipelines/my_pipeline.yaml` - Connect source to destination

2. Add required secrets to your `.env.{env}` file

3. Run validation:

   ```bash
   ingestion validate --pipeline my_pipeline --env dev
   ```

4. Execute the pipeline:
   ```bash
   ingestion run --pipeline my_pipeline --env dev
   ```
