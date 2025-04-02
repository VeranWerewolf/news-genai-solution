# News GenAI Network Debugging PowerShell Script

Write-Host "=== News GenAI Network Debugging Script ===" -ForegroundColor Cyan
Write-Host ""

# Check if containers are running
Write-Host "Checking if containers are running..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "=== Container Networks ===" -ForegroundColor Yellow
docker network ls | Select-String news-network -Context 0,3

Write-Host ""
Write-Host "=== Network Inspection ===" -ForegroundColor Yellow
docker network inspect news-network

Write-Host ""
Write-Host "=== API Container Logs ===" -ForegroundColor Yellow
docker-compose logs --tail=30 app

Write-Host ""
Write-Host "=== UI Container Logs ===" -ForegroundColor Yellow
docker-compose logs --tail=30 ui

Write-Host ""
Write-Host "=== Testing Network Connectivity ===" -ForegroundColor Yellow
# Test from UI to API container
Write-Host "Testing from UI to API container:" -ForegroundColor Magenta
docker-compose exec ui wget -O- --timeout=5 http://app:8000/health
if ($LASTEXITCODE -ne 0) {
    Write-Host "Connection failed" -ForegroundColor Red
}

# Test from API to Vector DB
Write-Host ""
Write-Host "Testing from API to Vector DB container:" -ForegroundColor Magenta
docker-compose exec app wget -O- --timeout=5 http://vector-db:6333/readiness
if ($LASTEXITCODE -ne 0) {
    Write-Host "Connection failed" -ForegroundColor Red
}

# Test from API to Ollama
Write-Host ""
Write-Host "Testing from API to Ollama container:" -ForegroundColor Magenta
docker-compose exec app wget -O- --timeout=5 http://ollama:11434/api/version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Connection failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Environment Variables ===" -ForegroundColor Yellow
Write-Host "UI container environment:" -ForegroundColor Magenta
docker-compose exec ui env | Select-String REACT_APP

Write-Host ""
Write-Host "API container environment:" -ForegroundColor Magenta
docker-compose exec app env | Select-String ALLOWED_ORIGINS
docker-compose exec app env | Select-String LLM_API_URL
docker-compose exec app env | Select-String VECTOR_DB

Write-Host ""
Write-Host "=== Debug complete ===" -ForegroundColor Green

# Keep PowerShell window open
Read-Host -Prompt "Press Enter to exit"