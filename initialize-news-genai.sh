#!/bin/bash

# News GenAI Solution Setup Script for Linux
# This script initializes and starts all containers for the News GenAI solution

echo -e "\e[1;36m=== News GenAI Solution Setup Script ===\e[0m"
echo ""

# Check for Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "\e[1;32mDocker detected: $DOCKER_VERSION\e[0m"
else
    echo -e "\e[1;31mERROR: Docker not found. Please install Docker for your Linux distribution.\e[0m"
    exit 1
fi

# Check for Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo -e "\e[1;32mDocker Compose detected: $COMPOSE_VERSION\e[0m"
else
    echo -e "\e[1;33mWARNING: Docker Compose command not found.\e[0m"
    echo -e "\e[1;33mMake sure Docker Compose is installed or available through the Docker CLI.\e[0m"
fi

echo ""

# Get current directory
CURRENT_DIR=$(pwd)

# Create necessary directories
echo -e "\e[1;33mCreating necessary directories...\e[0m"
directories=(
    "./vector-db/persistence"
    "./vector-db/snapshots"
    "./vector-db/config"
    "./huggingface-cache"
    "./ollama-data"
)

for dir in "${directories[@]}"; do
    FULL_PATH="$CURRENT_DIR/$dir"
    if [ ! -d "$FULL_PATH" ]; then
        mkdir -p "$FULL_PATH"
        echo -e "  \e[90mCreated directory: $FULL_PATH\e[0m"
    else
        echo -e "  \e[90mDirectory already exists: $FULL_PATH\e[0m"
    fi
done

# Verify directory permissions
echo ""
echo -e "\e[1;33mVerifying directory permissions...\e[0m"
for dir in "${directories[@]}"; do
    FULL_PATH="$CURRENT_DIR/$dir"
    if [ -w "$FULL_PATH" ]; then
        echo -e "  \e[90mDirectory has write permissions: $FULL_PATH\e[0m"
    else
        echo -e "  \e[1;33mWARNING: Directory may have permission issues: $FULL_PATH\e[0m"
        echo -e "  Attempting to fix permissions with: sudo chmod -R 777 $FULL_PATH"
        sudo chmod -R 777 "$FULL_PATH"
    fi
done

# Create .env file
echo ""
echo -e "\e[1;33mCreating .env file...\e[0m"
echo "LLM_API_URL=http://ollama:11434/api" > .env
echo -e "  \e[90mCreated .env file\e[0m"

# Start Ollama container standalone first to pull the model
echo ""
echo -e "\e[1;33mStarting Ollama container to download the Llama3 model...\e[0m"

# Check if container already exists
if [ "$(docker ps -a -q -f name=ollama-setup)" ]; then
    echo -e "  \e[90mRemoving existing ollama-setup container...\e[0m"
    docker rm -f ollama-setup >/dev/null
fi

# Start container with proper volume mapping
OLLAMA_DATA_PATH="$CURRENT_DIR/ollama-data"
docker run -d -v "${OLLAMA_DATA_PATH}:/root/.ollama" -p 11434:11434 --name ollama-setup ollama/ollama
echo -e "  \e[90mContainer started with volume: ${OLLAMA_DATA_PATH} -> /root/.ollama\e[0m"

# Wait for Ollama to start
echo -e "  \e[90mWaiting for Ollama to initialize...\e[0m"
sleep 10

# Check if Ollama is ready
MAX_RETRIES=5
RETRY_COUNT=0
OLLAMA_READY=false

while [ "$OLLAMA_READY" = false ] && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:11434/api/version >/dev/null; then
        OLLAMA_READY=true
        VERSION=$(curl -s http://localhost:11434/api/version | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        echo -e "  \e[1;32mOllama is ready! Version: $VERSION\e[0m"
    else
        RETRY_COUNT=$((RETRY_COUNT+1))
        echo -e "  \e[1;33mWaiting for Ollama to be ready (attempt $RETRY_COUNT of $MAX_RETRIES)...\e[0m"
        sleep 5
    fi
done

if [ "$OLLAMA_READY" = false ]; then
    echo -e "  \e[1;33mWARNING: Ollama service didn't respond in time. Continuing anyway...\e[0m"
fi

# Pull the llama3 model
echo ""
echo -e "\e[1;33mDownloading llama3 model (this may take a while)...\e[0m"
docker exec -it ollama-setup ollama pull llama3
if [ $? -eq 0 ]; then
    echo -e "  \e[1;32mModel downloaded successfully\e[0m"
else
    echo -e "  \e[1;33mWARNING: Model download may have encountered issues\e[0m"
fi

# List available models to verify
echo ""
echo -e "\e[1;33mVerifying available models:\e[0m"
docker exec ollama-setup ollama list
if [ $? -ne 0 ]; then
    echo -e "  \e[1;33mWARNING: Could not list models\e[0m"
fi

# Stop and remove the temporary container
echo ""
echo -e "\e[1;33mCleaning up temporary container...\e[0m"
docker stop ollama-setup >/dev/null
docker rm ollama-setup >/dev/null
echo -e "  \e[90mTemporary container removed\e[0m"

# Update requirements.txt to fix dependency issues
echo ""
echo -e "\e[1;33mUpdating requirements.txt to fix dependency issues...\e[0m"
REQUIREMENTS_PATH="app/requirements.txt"
if [ -f "$REQUIREMENTS_PATH" ]; then
    sed -i 's/langchain-core==0.1.12/langchain-core>=0.1.16/g' "$REQUIREMENTS_PATH"
    echo -e "  \e[90mUpdated langchain-core version requirement\e[0m"
fi

# Start all services with Docker Compose
echo ""
echo -e "\e[1;33mStarting all services with Docker Compose...\e[0m"
docker-compose up -d

# Check if all containers are running
echo ""
echo -e "\e[1;33mChecking container status...\e[0m"
sleep 5
docker-compose ps

echo -e "\e[1;36m=== Ollama Integration Test Script ===\e[0m"
echo ""

# Check if Ollama container is running
echo -e "\e[1;33mChecking if Ollama container is running...\e[0m"
if docker ps --filter "name=ollama" --format "{{.Names}}" | grep -q "ollama"; then
    echo -e "  \e[1;32mOllama container is running\e[0m"
else
    echo -e "  \e[1;31mERROR: Ollama container is not running!\e[0m"
    echo -e "  \e[1;33mStarting Ollama container...\e[0m"
    docker-compose up -d ollama
    sleep 10
fi

echo ""
echo -e "\e[1;33mTesting Ollama API...\e[0m"

# Check if Ollama API is responding
if curl -s http://localhost:11434/api/version >/dev/null; then
    VERSION=$(curl -s http://localhost:11434/api/version | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    echo -e "  \e[1;32mOllama API is responding. Version: $VERSION\e[0m"
else
    echo -e "  \e[1;31mERROR: Ollama API is not responding\e[0m"
    exit 1
fi

# Check available models
echo ""
echo -e "\e[1;33mChecking available models...\e[0m"
MODELS_LIST=$(docker exec ollama ollama list)
echo -e "  \e[1;32mAvailable models:\e[0m"
echo -e "$MODELS_LIST" | sed 's/^/  /'

# Check if llama3 model is available
if echo "$MODELS_LIST" | grep -q "llama3"; then
    echo -e "  \e[1;32mllama3 model is available!\e[0m"
else
    echo -e "  \e[1;33mWARNING: llama3 model not found. Attempting to pull it...\e[0m"
    docker exec ollama ollama pull llama3
fi

# Test generation with llama3 model
echo ""
echo -e "\e[1;33mTesting text generation with llama3 model...\e[0m"

TEST_REQUEST='{
  "model": "llama3",
  "prompt": "Say hello world in one sentence.",
  "options": {
    "temperature": 0.1,
    "num_predict": 100
  },
  "stream": false
}'

if RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate -d "$TEST_REQUEST" -H "Content-Type: application/json"); then
    echo -e "  \e[1;32mText generation successful!\e[0m"
    GENERATED_TEXT=$(echo $RESPONSE | grep -o '"response":"[^"]*"' | cut -d'"' -f4)
    echo -e "  Response from llama3: $GENERATED_TEXT"
else
    echo -e "  \e[1;31mERROR: Text generation failed\e[0m"
    
    # Try to pull the model again if generation failed
    echo -e "  \e[1;33mAttempting to pull llama3 model again...\e[0m"
    docker exec ollama ollama pull llama3
fi

# Display all volume mappings from docker-compose
echo ""
echo -e "\e[1;33mChecking volume mappings from docker-compose...\e[0m"
docker-compose config | grep -A 1 volumes

echo ""
echo -e "\e[1;36mIntegration test complete!\e[0m"

echo ""
echo -e "\e[1;32mSetup complete!\e[0m"
echo ""
echo -e "\e[1;36mAccess points:\e[0m"
echo -e "  API Documentation: http://localhost:8000/docs"
echo -e "  User Interface: http://localhost:3000"
echo -e "  Vector Database UI: http://localhost:6333/dashboard"
echo ""
echo -e "\e[1;33mNote: The first request to the API might take longer as the Llama3 model initializes.\e[0m"

# Make the script executable
chmod +x initialize-news-genai.sh