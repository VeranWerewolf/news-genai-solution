# Rebuild News GenAI App Container Script

Write-Host "=== Rebuilding News GenAI App Container ===" -ForegroundColor Cyan
Write-Host ""

# Stop all containers
Write-Host "Stopping all containers..." -ForegroundColor Yellow
docker-compose down
Write-Host "  All containers stopped" -ForegroundColor Green

# Rebuild the app container
Write-Host ""
Write-Host "Rebuilding app container..." -ForegroundColor Yellow
docker-compose build app
Write-Host "  App container rebuilt" -ForegroundColor Green

# Start all services
Write-Host ""
Write-Host "Starting all services..." -ForegroundColor Yellow
docker-compose up -d
Write-Host "  All services started" -ForegroundColor Green

# Wait a bit for services to initialize
Write-Host ""
Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check container status
Write-Host ""
Write-Host "Checking container status..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "Rebuild process completed!" -ForegroundColor Green
Write-Host ""
Write-Host "If the app container is still failing, check the logs with:" -ForegroundColor Cyan
Write-Host "  docker-compose logs app" -ForegroundColor White
Write-Host ""
Write-Host "Access points:" -ForegroundColor Cyan
Write-Host "  API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  User Interface: http://localhost:3000" -ForegroundColor White

# Keep console open
Read-Host -Prompt "Press Enter to exit"