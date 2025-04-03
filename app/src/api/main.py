from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from pydantic import BaseModel, field_validator
from typing import List, Optional, Union, Any
import urllib.parse

from ..scraper.extractor import NewsExtractor
from ..genai.analyzer import ArticleAnalyzer
from ..database.vector_store import VectorDatabase
from ..search.semantic_search import SemanticSearch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="News GenAI API",
    description="API for news extraction, analysis, and semantic search",
    version="1.0.0"
)

# Get allowed origins from environment or use default
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://ui:3000").split(",")
logger.info(f"Allowing CORS from origins: {allowed_origins}")

# Add CORS middleware with specific allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for debugging
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Create instances of components
news_extractor = NewsExtractor()
article_analyzer = ArticleAnalyzer()
vector_db = VectorDatabase()
semantic_search = SemanticSearch()

# Define request and response models
class UrlListRequest(BaseModel):
    urls: List[str]
    
    class Config:
        schema_extra = {
            "example": {
                "urls": ["https://example.com/article1", "https://example.com/article2"]
            }
        }
    
    @field_validator('urls')
    @classmethod
    def validate_urls(cls, v):
        valid_urls = []
        for url in v:
            try:
                # Basic URL validation
                parsed = urllib.parse.urlparse(url)
                if parsed.scheme and parsed.netloc:
                    valid_urls.append(url)
                else:
                    logger.warning(f"Skipping invalid URL: {url}")
            except Exception as e:
                logger.warning(f"Error validating URL {url}: {e}")
        
        if not valid_urls:
            raise ValueError("No valid URLs provided")
        return valid_urls

class SearchRequest(BaseModel):
    query: str
    enhance: bool = True
    limit: int = 5

class ArticleResponse(BaseModel):
    url: str
    title: str
    summary: Optional[str] = None
    topics: Optional[List[str]] = None

# API routes
@app.get("/")
async def root():
    return {"message": "Welcome to the News GenAI API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/extract", response_model=List[ArticleResponse])
async def extract_articles(request: UrlListRequest):
    """Extract articles from the provided URLs."""
    try:
        logger.info(f"Extracting articles from {len(request.urls)} URLs")
        # Extract articles
        articles = news_extractor.extract_from_urls(request.urls)
        if not articles:
            logger.warning("No articles could be extracted")
            raise HTTPException(status_code=404, detail="No articles could be extracted")
            
        logger.info(f"Successfully extracted {len(articles)} articles")
        return articles
    except Exception as e:
        logger.error(f"Error extracting articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=List[ArticleResponse])
async def analyze_articles(request: UrlListRequest):
    """Extract and analyze articles from the provided URLs."""
    try:
        logger.info(f"Analyzing articles from {len(request.urls)} URLs")
        # Extract articles
        articles = news_extractor.extract_from_urls(request.urls)
        if not articles:
            logger.warning("No articles could be extracted")
            raise HTTPException(status_code=404, detail="No articles could be extracted")
            
        # Analyze articles
        analyzed_articles = article_analyzer.analyze_articles(articles)
        logger.info(f"Successfully analyzed {len(analyzed_articles)} articles")
            
        return analyzed_articles
    except Exception as e:
        logger.error(f"Error analyzing articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/store", response_model=List[str])
async def store_articles(request: UrlListRequest):
    """Extract, analyze, and store articles from the provided URLs."""
    try:
        logger.info(f"Processing and storing articles from {len(request.urls)} URLs")
        # Extract articles
        articles = news_extractor.extract_from_urls(request.urls)
        if not articles:
            logger.warning("No articles could be extracted")
            raise HTTPException(status_code=404, detail="No articles could be extracted")
            
        # Analyze articles
        analyzed_articles = article_analyzer.analyze_articles(articles)
        
        # Store articles
        article_ids = vector_db.store_articles(analyzed_articles)
        logger.info(f"Successfully stored {len(article_ids)} articles")
            
        return article_ids
    except Exception as e:
        logger.error(f"Error storing articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=List[ArticleResponse])
async def search_articles(request: SearchRequest):
    """Search for articles matching the query."""
    try:
        logger.info(f"Searching for articles with query: '{request.query}'")
        # Perform search
        results = semantic_search.search(
            query=request.query,
            enhance=request.enhance,
            limit=request.limit
        )
        
        logger.info(f"Search returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Error searching articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))