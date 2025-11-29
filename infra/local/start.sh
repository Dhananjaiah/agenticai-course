#!/bin/bash

# Local development startup script
# This script starts the application locally for development

set -e

echo "=== Agentic AI Insurance Assistant - Local Development ==="
echo ""

# Navigate to project root
cd "$(dirname "$0")/../.."

# Check if we should use Docker
if [ "$1" == "--docker" ]; then
    echo "Starting with Docker Compose..."
    cd infra/local
    docker-compose up --build
else
    echo "Starting with uvicorn directly..."
    echo ""
    
    # Set environment variables for local development
    export ENV=local
    export POLICY_DB_URL=sqlite:///policy.db
    export CLAIMS_DB_URL=sqlite:///claims.db
    export DOCS_STORE_TYPE=mock
    export LLM_API_KEY=""
    export LLM_BYPASS=true
    
    # Check if virtualenv exists
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    # Install dependencies if needed
    pip install -r backend/requirements.txt --quiet
    
    echo "Starting server on http://localhost:8000"
    echo "API docs available at http://localhost:8000/docs"
    echo ""
    
    # Start uvicorn with hot reload for development
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
fi
