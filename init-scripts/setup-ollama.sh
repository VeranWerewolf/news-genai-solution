#!/bin/bash

# Script to help set up Ollama with the required model
set -e

echo "=== Ollama Setup Script ==="
echo ""
echo "This script will help you set up Ollama with the llama3 model."
echo ""

# Check for Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not found. Please install Docker."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "Docker and Docker Compose detected."

# Create necessary directories
mkdir -p vector-db/persistence
mkdir -p vector-db/snapshots
mkdir -p vector-db/config
mkdir -p postgres-data
mkdir -p grafana-data

# Create .env file
echo ""
echo "Creating .env file..."
cat > .env << EOL
LLM_API_URL=http://ollama:11434/api
EOL

# Start Ollama container standalone first to pull the model
echo ""
echo "Starting Ollama container to download the model..."
docker run -d -v ollama_data:/root/.ollama -p 11434:11434 --name ollama-setup ollama/ollama
sleep 5  # Wait for Ollama to start

# Pull the llama3 model
echo ""
echo "Downloading llama3 model (this may take a while)..."
docker exec -it ollama-setup ollama pull llama3

# Stop and remove the temporary container
echo ""
echo "Cleaning up temporary container..."
docker stop ollama-setup
docker rm ollama-setup

echo ""
echo "Setup complete!"
echo ""
echo "To start all services, run:"
echo "docker-compose up -d"
echo ""
echo "Note: The first startup may take a minute as Ollama initializes."