#!/bin/bash
# Setup and start Prefect server for local orchestration

set -e

echo "========================================"
echo "PREFECT SERVER SETUP"
echo "========================================"
echo ""

# Check if Prefect is installed
if ! command -v prefect &> /dev/null; then
    echo "❌ Prefect is not installed"
    echo "Run: pip install prefect prefect-dask"
    exit 1
fi

echo "✓ Prefect is installed"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Initialize Prefect database
echo "Initializing Prefect database..."
prefect server database reset -y 2>/dev/null || true

echo ""
echo "========================================"
echo "STARTING PREFECT SERVER"
echo "========================================"
echo ""
echo "The Prefect UI will be available at:"
echo "  http://127.0.0.1:4200"
echo ""
echo "In another terminal, run:"
echo "  1. Deploy flows:"
echo "     source venv/bin/activate"
echo "     python -m orchestration.flows --deploy"
echo ""
echo "  2. Start a worker:"
echo "     prefect worker start --pool default"
echo ""
echo "  3. Or run flows directly:"
echo "     python -m orchestration.flows --github-user torvalds"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Prefect server
prefect server start --host 0.0.0.0 --port 4200
