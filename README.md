# News GenAI Solution with Ollama

A containerized solution for news article scraping, AI-powered analysis using locally-hosted Llama3, and semantic search.

## Features
- News extraction from provided URLs
- Llama3-driven summarization and topic identification via Ollama
- Semantic search with vector database integration
- Fully containerized deployment with local LLM

## Architecture
This solution uses a microservices architecture with Docker containers:
- Application container: Core functionality for scraping and AI processing
- Ollama container: Runs the Llama3 model locally
- Vector database container: Stores article embeddings and metadata
- UI container: Web interface for demonstration

## Technical Details
- **News Extraction**: Custom Python scraper using BeautifulSoup for content extraction
- **GenAI Analysis**: Locally-hosted Llama3 model via Ollama for summarization and topic extraction
- **Vector Storage**: Qdrant vector database for efficient semantic search
- **Embeddings**: Sentence Transformers for creating vector embeddings
- **API Layer**: FastAPI for REST endpoints
- **UI**: React.js with Tailwind CSS

## Prerequisites
- Docker and Docker Compose
- At least 8GB of RAM for CPU-only mode
- At least 20GB of free disk space

## Setup and Usage

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/news-genai-solution.git
cd news-genai-solution
```

### 2. Setup Ollama with the required model
The setup script will download the Llama3 model via Ollama:

```bash
# For Windows:
./initialize-news-genai.ps1

# For Linux/Mac:
chmod +x setup-ollama.sh
./setup-ollama.sh
```

### 3. Start the services
Once the setup is complete, start all services:

```bash
docker-compose up -d
```

This will start all the required containers:
- ollama: The Ollama service running the Llama3 model locally
- app: The FastAPI application for news extraction and analysis
- vector-db: Qdrant vector database for semantic search
- ui: The user interface

### 4. Access the services
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- UI: http://localhost:3000
- Vector Database UI: http://localhost:6333/dashboard
- Grafana Monitoring: http://localhost:3001

## API Endpoints

### Extract Articles
```
POST /extract
```
Extracts articles from provided URLs without applying GenAI analysis.

### Analyze Articles
```
POST /analyze
```
Extracts and analyzes articles using the local Llama3 model to generate summaries and identify topics.

### Store Articles
```
POST /store
```
Extracts, analyzes, and stores articles in the vector database for later retrieval.

### Search Articles
```
POST /search
```
Searches for articles using semantic search powered by sentence transformers embeddings and Llama3 query enhancement.

### Find Topics
```
POST /topics
```
Searches for topics related to the query.

### Get Articles by Topic
```
GET /articles/by-topic/{topic}
```
Retrieves articles tagged with a specific topic.

### Get Similar Articles
```
GET /articles/similar/{article_id}
```
Finds articles that are semantically similar to the given article.

## Using GPU Acceleration (Optional)

The default setup uses CPU-only mode for Ollama. If you have a compatible NVIDIA GPU, you can enable GPU acceleration by:

1. Installing the NVIDIA Container Toolkit:
```bash
# For Ubuntu/Debian
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

2. Configure Docker to use NVIDIA:
```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

3. Update the `docker-compose.yml` file to enable GPU support (uncomment the deploy section).

## Performance Notes
- CPU-only mode will be significantly slower than GPU-accelerated mode
- The first request to the model might take longer as Ollama loads the model into memory
- For production use, consider using a more powerful server or enabling GPU acceleration

## Troubleshooting

### Model Loading Issues
- Check Ollama logs: `docker logs ollama`
- Ensure you have enough disk space and RAM
- If using GPU, verify that NVIDIA drivers are properly installed

### API Connection Issues
- Ensure all containers are running with `docker-compose ps`
- Check application logs: `docker logs news-genai-solution_app_1`

### Network Debugging
For Windows:
```
./debug-network.ps1
```

For Linux/Mac:
```
chmod +x debug-network.sh
./debug-network.sh
```

## License
MIT License - see LICENSE file for details