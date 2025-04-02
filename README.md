# News GenAI Solution

A containerized solution for news article scraping, AI-powered analysis, and semantic search.

## Features
- News extraction from provided URLs
- GenAI-driven summarization and topic identification
- Semantic search with vector database integration
- Fully containerized deployment

## Setup and Usage
1. Clone this repository
2. Configure your API keys in the \.env\ file
3. Run \docker-compose up\ to start all services
4. Access the API at http://localhost:8000
5. Access the UI at http://localhost:3000

## Architecture
This solution uses a microservices architecture with Docker containers:
- Application container: Core functionality for scraping and AI processing
- Vector database container: Stores article embeddings and metadata
- UI container: Optional web interface for demonstration

## API Documentation
API documentation is available at http://localhost:8000/docs when the service is running.
