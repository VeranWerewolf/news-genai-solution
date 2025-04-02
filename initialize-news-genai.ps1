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

# Start container
docker run -d -v ollama_data:/root/.ollama -p 11434:11434 --name ollama-setup ollama/ollama
Write-Host "  Container started" -ForegroundColor Gray

# Wait for Ollama to start
Write-Host "  Waiting for Ollama to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Pull the llama3 model
Write-Host ""
Write-Host "Downloading llama3 model (this may take a while)..." -ForegroundColor Yellow
docker exec -it ollama-setup ollama pull llama3
Write-Host "  Model downloaded successfully" -ForegroundColor Green

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

Read-Host