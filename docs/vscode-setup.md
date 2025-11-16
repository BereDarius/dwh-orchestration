# VS Code Configuration

This document describes the VS Code setup and features available in the Data Ingestion Framework.

## Overview

The project includes a fully configured VS Code workspace with:

- **13 recommended extensions**
- **Auto-formatting and linting on save**
- **YAML schema validation** for all config files
- **10+ pre-configured tasks**
- **6 debug configurations**
- **Type checking** in strict mode
- **Test coverage** visualization

## Getting Started

### 1. Open the Workspace

```bash
code data-ingestion-framework.code-workspace
```

Or from VS Code: `File → Open Workspace from File...`

### 2. Install Extensions

When you open the workspace, VS Code will prompt you to install recommended extensions. Click **Install All** to get:

#### Python Development

- `ms-python.python` - Python language support
- `ms-python.vscode-pylance` - Fast, feature-rich Python language server
- `ms-python.black-formatter` - Black code formatter
- `ms-python.isort` - Import statement organizer
- `charliermarsh.ruff` - Fast Python linter

#### Configuration & DevOps

- `redhat.vscode-yaml` - YAML language support with validation
- `ms-azuretools.vscode-docker` - Docker integration

#### Code Quality & Productivity

- `eamodio.gitlens` - Enhanced Git integration
- `aaron-bond.better-comments` - Colorful comment highlighting
- `usernamehw.errorlens` - Inline error/warning display
- `christian-kohler.path-intellisense` - File path autocomplete
- `gruntfuggly.todo-tree` - TODO/FIXME comment tracker
- `ryanluker.vscode-coverage-gutters` - Test coverage visualization

## Features

### Auto-Formatting

**Python files** are automatically formatted on save using:

- **Black** (line length: 100)
- **isort** for import organization

**YAML files** are formatted on save with:

- 2-space indentation
- Consistent spacing

### YAML Schema Validation

All YAML configuration files have **auto-completion and validation**:

#### Source Files (`config/**/sources/*.yaml`)

- Schema: `.vscode/schemas/source-schema.json`
- Validates: source type, auth config, resources, incremental settings
- IntelliSense provides field suggestions and documentation

#### Destination Files (`config/**/destinations/*.yaml`)

- Schema: `.vscode/schemas/destination-schema.json`
- Validates: destination type, connection settings, table format
- Hover over fields for descriptions

#### Pipeline Files (`config/**/pipelines/*.yaml`)

- Schema: `.vscode/schemas/pipeline-schema.json`
- Validates: source/destination refs, cron expressions, SLA settings
- Real-time error highlighting

**Example:** When typing in a pipeline YAML:

```yaml
pipeline:
  name: my_pipeline # Auto-complete suggests valid field names
  environment: # Auto-complete shows: dev, stage, prod
  schedule:
    cron: # Hover shows: "Cron expression for scheduling"
```

### Linting

**Ruff** runs automatically on save and shows:

- Code style issues
- Potential bugs
- Unused imports
- Complexity warnings

**Error Lens** displays errors inline (no need to hover).

### Type Checking

**Pylance** runs in **strict mode** providing:

- Type inference
- Auto-imports
- Parameter hints
- Definition peeking
- Reference finding

### Test Coverage

**Coverage Gutters** shows test coverage directly in the editor:

- Green gutters = covered lines
- Red gutters = uncovered lines
- Click the **Watch** button in the status bar to enable

After running tests with coverage:

```bash
pytest --cov=src --cov-report=html
```

The coverage appears automatically in your Python files.

## Tasks

Access via: `Cmd+Shift+P` → `Tasks: Run Task`

### Testing Tasks

| Task                    | Description                   | Shortcut          |
| ----------------------- | ----------------------------- | ----------------- |
| Run Tests               | Run pytest without coverage   | -                 |
| Run Tests with Coverage | Run with HTML coverage report | Default test task |

### Code Quality Tasks

| Task        | Description                             |
| ----------- | --------------------------------------- |
| Format Code | Run Black and isort on all Python files |
| Lint Code   | Run Ruff linter                         |
| Type Check  | Run mypy type checker                   |

### Configuration Tasks

| Task                   | Description                  | Environment Input    |
| ---------------------- | ---------------------------- | -------------------- |
| Validate Configs       | Validate all YAML configs    | Yes (dev/stage/prod) |
| List All Configs       | Show detailed config listing | Yes                  |
| Discover Configs (CLI) | Run discovery command        | Yes                  |
| Switch Environment     | Switch active environment    | Yes                  |

### Setup Tasks

| Task           | Description                              |
| -------------- | ---------------------------------------- |
| Setup Project  | Run `scripts/setup.sh` for initial setup |
| Run Quickstart | Verify installation with `quickstart.py` |

## Debug Configurations

Access via: `F5` or Debug panel (Cmd+Shift+D)

### Execution Configs

**Python: Current File**

- Debug any Python file
- Sets ENVIRONMENT=dev and PYTHONPATH

**Run Pipeline (Dev)**

- Debug the YouTube pipeline
- Runs: `ingestion.cli run --pipeline youtube_to_databricks --env dev`
- Full debugging with breakpoints

**List Pipelines**

- Debug pipeline listing
- Runs: `ingestion.cli list-pipelines --env dev`

**Discover All Configs**

- Debug config discovery
- Runs: `ingestion.cli discover --env dev`

### Testing Configs

**Run Tests with Coverage**

- Debug all tests with coverage
- Runs: `pytest tests -v --cov=src --cov-report=html`
- Set breakpoints in test files

**Run Current Test File**

- Debug the currently open test file
- Fast iteration on specific tests

## Settings

Key VS Code settings configured for this project:

### Python Settings

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.analysis.typeCheckingMode": "strict",
  "python.testing.pytestEnabled": true
}
```

### Formatting Settings

```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  }
}
```

### YAML Settings

```json
{
  "[yaml]": {
    "editor.formatOnSave": true,
    "editor.tabSize": 2
  },
  "yaml.validate": true,
  "yaml.completion": true
}
```

## Keyboard Shortcuts

| Action           | Shortcut (Mac)        | Shortcut (Windows/Linux) |
| ---------------- | --------------------- | ------------------------ |
| Run Task         | `Cmd+Shift+P` → Tasks | `Ctrl+Shift+P` → Tasks   |
| Debug            | `F5`                  | `F5`                     |
| Run Tests        | `Cmd+Shift+P` → Test  | `Ctrl+Shift+P` → Test    |
| Format Document  | `Shift+Option+F`      | `Shift+Alt+F`            |
| Organize Imports | `Shift+Option+O`      | `Shift+Alt+O`            |
| Go to Definition | `F12`                 | `F12`                    |
| Find References  | `Shift+F12`           | `Shift+F12`              |
| Peek Definition  | `Option+F12`          | `Alt+F12`                |

## Tips & Tricks

### 1. Quick Config Validation

1. Open any YAML config file
2. Edit a value
3. See validation errors immediately
4. Hover over fields for documentation

### 2. Fast Testing Workflow

1. Write a test in `tests/`
2. Set breakpoint
3. Press `F5` → Select "Run Current Test File"
4. Debug directly in VS Code

### 3. Coverage Workflow

1. Run: Tasks → Run Tests with Coverage
2. Click "Watch" in status bar
3. Edit Python file
4. See coverage update automatically

### 4. Todo Tracking

Install Todo Tree extension and view all TODOs:

- `Cmd+Shift+P` → `Todo Tree: Focus on Todo Tree View`
- Automatically finds TODO, FIXME, BUG comments

### 5. Git Integration

GitLens provides:

- Inline blame annotations
- Line history
- File history
- Compare branches
- And much more!

## Troubleshooting

### Extensions Not Installing

Manually install from VS Code Marketplace:

```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
# ... etc
```

### Formatting Not Working

1. Check virtual environment is activated: `.venv`
2. Ensure Black is installed: `pip install black`
3. Check settings: `Cmd+,` → search "format on save"

### YAML Validation Not Working

1. Check YAML extension is installed
2. Verify schema files exist in `.vscode/schemas/`
3. Check workspace settings reference correct paths

### Tests Not Discovered

1. Check Python interpreter: Click Python version in status bar
2. Select: `.venv/bin/python`
3. Check pytest is installed: `pip install pytest`
4. Reload window: `Cmd+Shift+P` → `Reload Window`

## Customization

### Add Custom Tasks

Edit `.vscode/tasks.json`:

```json
{
  "label": "My Custom Task",
  "type": "shell",
  "command": "echo Hello",
  "group": "none"
}
```

### Add Debug Configuration

Edit `.vscode/launch.json`:

```json
{
  "name": "My Debug Config",
  "type": "debugpy",
  "request": "launch",
  "program": "${workspaceFolder}/my_script.py",
  "console": "integratedTerminal"
}
```

### Modify Schemas

Edit JSON schema files in `.vscode/schemas/` to customize YAML validation.

## Resources

- [VS Code Python Tutorial](https://code.visualstudio.com/docs/python/python-tutorial)
- [VS Code YAML Extension](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)
- [Debugging in VS Code](https://code.visualstudio.com/docs/editor/debugging)
- [Tasks in VS Code](https://code.visualstudio.com/docs/editor/tasks)
