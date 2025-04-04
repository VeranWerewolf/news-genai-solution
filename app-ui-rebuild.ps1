# Rebuild News GenAI App with Vector DB Only Setup

Write-Host "=== Rebuilding News GenAI Solution (Vector DB Only) ===" -ForegroundColor Cyan
Write-Host ""

# Stop all containers
Write-Host "Stopping all containers..." -ForegroundColor Yellow
docker-compose down
Write-Host "  All containers stopped" -ForegroundColor Green

# Verify that all required directories exist
Write-Host ""
Write-Host "Verifying required directories..." -ForegroundColor Yellow
$directories = @(
    "./vector-db/persistence",
    "./vector-db/snapshots",
    "./vector-db/config",
    "./huggingface-cache",
    "./ollama-data"
)

$currentDir = Get-Location
foreach ($dir in $directories) {
    $fullPath = Join-Path -Path $currentDir -ChildPath $dir
    if (-not (Test-Path $fullPath)) {
        Write-Host "  Creating missing directory: $dir" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    } else {
        Write-Host "  Directory exists: $dir" -ForegroundColor Green
    }
}

# Rebuild the app container
Write-Host ""
Write-Host "Rebuilding app container..." -ForegroundColor Yellow
docker-compose build app
Write-Host "  App container rebuilt" -ForegroundColor Green

# Verify volume paths in docker-compose
Write-Host ""
Write-Host "Checking volume mappings from docker-compose..." -ForegroundColor Yellow
docker-compose config | Select-String -Pattern "volume" -Context 0,1

# Start all services
Write-Host ""
Write-Host "Starting all services..." -ForegroundColor Yellow
docker-compose up -d
Write-Host "  All services started" -ForegroundColor Green

# Wait a bit for services to initialize
Write-Host ""
Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check container status
Write-Host ""
Write-Host "Checking container status..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "Rebuild process completed!" -ForegroundColor Green
Write-Host ""
Write-Host "If containers are still failing, check the logs with:" -ForegroundColor Cyan
Write-Host "  docker-compose logs app" -ForegroundColor White
Write-Host "  docker-compose logs ui" -ForegroundColor White
Write-Host ""
Write-Host "Access points:" -ForegroundColor Cyan
Write-Host "  API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  User Interface: http://localhost:3000" -ForegroundColor White
Write-Host "  Vector Database UI: http://localhost:6333/dashboard" -ForegroundColor White

# Keep console open
Read-Host -Prompt "Press Enter to exit"