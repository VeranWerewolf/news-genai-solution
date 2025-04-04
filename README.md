# News GenAI Solution with Ollama

A containerized solution for news article scraping, AI-powered analysis using locally-hosted Llama3, and semantic search.

## Roadmap
- Add chanking to the news articles if the amount of the tokens is exceeded (just trimming content for now) 
- Add GPU support for ollama models to process information faster (only CPU-mode is available)
- Implement SentenceTransformer:Load cache to speed up the initialization of the App container

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

### 2. Setup using script
The setup script will initialize all required containers:

Run:
Windows: initialize-news-genai.ps1
Linux: initialize-news-genai.sh

### 3. Access the services
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- UI: http://localhost:3000
- Vector Database UI: http://localhost:6333/dashboard

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

## Using GPU Acceleration (TBD)

The default setup uses CPU-only mode for Ollama. GPU-mode will be implemented later

## Performance Notes
- Every time the backend starts it can take 2-3 minutes to download requred data
- CPU-only mode will be significantly slower than GPU-accelerated mode
- The first request to the model might take longer as Ollama loads the model into memory
- For production use, consider using a more powerful server or enabling GPU acceleration

## Troubleshooting
 - In the UI app you can check System Status to see what 

### Model Loading Issues
- Check Ollama logs: `docker logs ollama`
- Ensure you have enough disk space and RAM

### API Connection Issues
- Ensure all containers are running with `docker-compose ps`
- Check application logs

## License
MIT License - see LICENSE file for details
