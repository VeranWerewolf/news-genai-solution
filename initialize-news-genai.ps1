# News GenAI Solution Setup Script
# This script initializes and starts all containers for the News GenAI solution

Write-Host "=== News GenAI Solution Setup Script ===" -ForegroundColor Cyan
Write-Host ""

# Check for Docker
try {
    $dockerVersion = docker --version
    Write-Host "Docker detected: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker not found. Please install Docker Desktop for Windows." -ForegroundColor Red
    exit 1
}

# Check for Docker Compose
try {
    $composeVersion = docker-compose --version
    Write-Host "Docker Compose detected: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Docker Compose command not found." -ForegroundColor Yellow
    Write-Host "Docker Desktop for Windows typically includes Docker Compose functionality." -ForegroundColor Yellow
}

Write-Host ""

# Create necessary directories
Write-Host "Creating necessary directories..." -ForegroundColor Yellow
$directories = @(
    "vector-db/persistence",
    "vector-db/snapshots",
    "vector-db/config",
    "postgres-data",
    "grafana-data"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created directory: $dir" -ForegroundColor Gray
    } else {
        Write-Host "  Directory already exists: $dir" -ForegroundColor Gray
    }
}

# Create .env file
Write-Host ""
Write-Host "Creating .env file..." -ForegroundColor Yellow
@"
LLM_API_URL=http://ollama:11434/api
"@ | Out-File -FilePath .env -Encoding utf8 -Force
Write-Host "  Created .env file" -ForegroundColor Gray

# Start Ollama container standalone first to pull the model
Write-Host ""
Write-Host "Starting Ollama container to download the Llama3 model..." -ForegroundColor Yellow

# Check if container already exists
$containerExists = docker ps -a --filter "name=ollama-setup" --format "{{.Names}}"
if ($containerExists -eq "ollama-setup") {
    Write-Host "  Removing existing ollama-setup container..." -ForegroundColor Gray
    docker rm -f ollama-setup | Out-Null
}

# Create a volume for Ollama data if it doesn't exist
docker volume create ollama_data

# Start container
docker run -d -v ollama_data:/root/.ollama -p 11434:11434 --name ollama-setup ollama/ollama
Write-Host "  Container started" -ForegroundColor Gray

# Wait for Ollama to start
Write-Host "  Waiting for Ollama to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# Check if Ollama is ready
$maxRetries = 5
$retryCount = 0
$ollamaReady = $false

while (-not $ollamaReady -and $retryCount -lt $maxRetries) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -Method Get -ErrorAction SilentlyContinue
        if ($response) {
            $ollamaReady = $true
            Write-Host "  Ollama is ready! Version: $($response.version)" -ForegroundColor Green
        }
    } catch {
        $retryCount++
        Write-Host "  Waiting for Ollama to be ready (attempt $retryCount of $maxRetries)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

if (-not $ollamaReady) {
    Write-Host "  WARNING: Ollama service didn't respond in time. Continuing anyway..." -ForegroundColor Yellow
}

# Pull the llama3 model
Write-Host ""
Write-Host "Downloading llama3 model (this may take a while)..." -ForegroundColor Yellow
docker exec -it ollama-setup ollama pull llama3
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Model downloaded successfully" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Model download may have encountered issues" -ForegroundColor Yellow
}

# List available models to verify
Write-Host ""
Write-Host "Verifying available models:" -ForegroundColor Yellow
docker exec ollama-setup ollama list
if ($LASTEXITCODE -ne 0) {
    Write-Host "  WARNING: Could not list models" -ForegroundColor Yellow
}

# Stop and remove the temporary container
Write-Host ""
Write-Host "Cleaning up temporary container..." -ForegroundColor Yellow
docker stop ollama-setup | Out-Null
docker rm ollama-setup | Out-Null
Write-Host "  Temporary container removed" -ForegroundColor Gray

# Update requirements.txt to fix dependency issues
Write-Host ""
Write-Host "Updating requirements.txt to fix dependency issues..." -ForegroundColor Yellow
$requirementsPath = "app/requirements.txt"
if (Test-Path $requirementsPath) {
    $requirements = Get-Content $requirementsPath
    $updatedRequirements = $requirements -replace "langchain-core==0.1.12", "langchain-core>=0.1.16"
    $updatedRequirements | Set-Content $requirementsPath -Force
    Write-Host "  Updated langchain-core version requirement" -ForegroundColor Gray
}

# Start all services with Docker Compose
Write-Host ""
Write-Host "Starting all services with Docker Compose..." -ForegroundColor Yellow
docker-compose up -d

# Check if all containers are running
Write-Host ""
Write-Host "Checking container status..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
docker-compose ps

# Ollama Integration Test Script
# This script tests if Ollama is properly set up with the llama3 model

Write-Host "=== Ollama Integration Test Script ===" -ForegroundColor Cyan
Write-Host ""

# Check if Ollama container is running
Write-Host "Checking if Ollama container is running..." -ForegroundColor Yellow
$ollamaRunning = docker ps --filter "name=ollama" --format "{{.Names}}"
if ($ollamaRunning -eq "ollama") {
    Write-Host "  Ollama container is running" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Ollama container is not running!" -ForegroundColor Red
    Write-Host "  Starting Ollama container..." -ForegroundColor Yellow
    docker-compose up -d ollama
    Start-Sleep -Seconds 10
}

Write-Host ""
Write-Host "Testing Ollama API..." -ForegroundColor Yellow

# Check if Ollama API is responding
try {
    $versionResponse = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -Method Get -ErrorAction Stop
    Write-Host "  Ollama API is responding. Version: $($versionResponse.version)" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Ollama API is not responding: $_" -ForegroundColor Red
    exit 1
}

# Check available models
Write-Host ""
Write-Host "Checking available models..." -ForegroundColor Yellow
try {
    # First try to list models via CLI
    $modelsList = docker exec ollama ollama list
    Write-Host "  Available models:" -ForegroundColor Green
    Write-Host $modelsList -ForegroundColor White
    
    # Check if llama3 model is available
    if ($modelsList -match "llama3") {
        Write-Host "  llama3 model is available!" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: llama3 model not found. Attempting to pull it..." -ForegroundColor Yellow
        docker exec ollama ollama pull llama3
    }
} catch {
    Write-Host "  ERROR: Could not retrieve models: $_" -ForegroundColor Red
}

# Test generation with llama3 model
Write-Host ""
Write-Host "Testing text generation with llama3 model..." -ForegroundColor Yellow

$testRequest = @{
    model = "llama3"
    prompt = "Say hello world in one sentence."
    options = @{
        temperature = 0.1
        num_predict = 100
    }
    stream = $false
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $testRequest -ContentType "application/json" -ErrorAction Stop
    Write-Host "  Text generation successful!" -ForegroundColor Green
    Write-Host "  Response from llama3: $($response.response)" -ForegroundColor White
} catch {
    Write-Host "  ERROR: Text generation failed: $_" -ForegroundColor Red
    
    # Try to pull the model again if generation failed
    Write-Host "  Attempting to pull llama3 model again..." -ForegroundColor Yellow
    docker exec ollama ollama pull llama3
}

Write-Host ""
Write-Host "Integration test complete!" -ForegroundColor Cyan

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Access points:" -ForegroundColor Cyan
Write-Host "  API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  User Interface: http://localhost:3000" -ForegroundColor White
Write-Host "  Vector Database UI: http://localhost:6333/dashboard" -ForegroundColor White
Write-Host "  Grafana Monitoring: http://localhost:3001" -ForegroundColor White
Write-Host ""
Write-Host "Note: The first request to the API might take longer as the Llama3 model initializes." -ForegroundColor Yellow

# Keep console open
Read-Host -Prompt "Press Enter to exit"