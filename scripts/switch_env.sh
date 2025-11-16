#!/bin/bash
set -e

# Script to switch between environments (dev, stage, prod)

ENV=$1

if [ -z "$ENV" ]; then
    echo "Usage: ./switch_env.sh [dev|stage|prod]"
    exit 1
fi

# Validate environment
if [ "$ENV" != "dev" ] && [ "$ENV" != "stage" ] && [ "$ENV" != "prod" ]; then
    echo "Error: Invalid environment. Must be dev, stage, or prod"
    exit 1
fi

# Check if environment template exists
if [ ! -f ".env.$ENV.example" ]; then
    echo "Error: Environment template .env.$ENV.example not found"
    exit 1
fi

echo "Switching to $ENV environment..."

# Copy environment file
cp ".env.$ENV.example" ".env"
echo "✓ Copied .env.$ENV.example to .env"

# Update ENVIRONMENT variable in .env
if command -v sed &> /dev/null; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/ENVIRONMENT=.*/ENVIRONMENT=$ENV/" .env
    else
        # Linux
        sed -i "s/ENVIRONMENT=.*/ENVIRONMENT=$ENV/" .env
    fi
    echo "✓ Updated ENVIRONMENT variable"
fi

# Create symlink to docker-compose file
if [ -f "docker/$ENV/docker-compose.yml" ]; then
    ln -sf "docker/$ENV/docker-compose.yml" "docker-compose.yml"
    echo "✓ Updated docker-compose.yml symlink"
fi

echo ""
echo "✅ Switched to $ENV environment"
echo ""
echo "⚠️  IMPORTANT: Update .env with actual values for $ENV!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your $ENV credentials"
echo "2. Validate: python scripts/validate_secrets.py --env $ENV"
echo "3. Run pipeline: python -m ingestion.cli run --pipeline <name> --env $ENV"
echo ""
