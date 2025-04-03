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
    topics: Optional[List[str]] = None

class ArticleResponse(BaseModel):
    url: str
    title: str
    summary: Optional[str] = None
    topics: Optional[List[str]] = None
    source: Optional[str] = None
    date: Optional[str] = None

class TopicResponse(BaseModel):
    topic: str
    count: int

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
        
        # Check if query is empty
        if not request.query or request.query.strip() == "":
            logger.warning("Empty search query provided")
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        # First, if no topics are provided but we want enhanced search,
        # we can try to find relevant topics to improve search quality
        suggested_topics = []
        if request.enhance and (not request.topics or len(request.topics) == 0):
            try:
                suggested_topics = semantic_search.get_related_topics(request.query, limit=3)
                logger.info(f"Found suggested topics: {suggested_topics}")
                # We'll use these in search but not enforce them as filters
            except Exception as e:
                logger.warning(f"Error finding suggested topics: {e}")
        
        # Perform search with enhanced parameters
        results = semantic_search.search(
            query=request.query,
            enhance=request.enhance,
            limit=request.limit * 2,  # Get more results than needed for filtering
            filter_by_topics=request.topics  # Original topic filter
        )
        
        # Filter by topics if provided by user
        if request.topics and len(request.topics) > 0:
            filtered_results = [
                article for article in results
                if any(topic in article.get('topics', []) for topic in request.topics)
            ]
            
            # If we filtered out everything, try again without topic filtering
            if not filtered_results and results:
                logger.warning(f"Topic filtering removed all results, returning unfiltered results")
                filtered_results = results
            
            results = filtered_results
        
        # If we still have no results, try one last search with just the terms
        if not results:
            logger.warning(f"No results found with primary strategies, trying basic search")
            basic_results = semantic_search.vector_db.search(
                query=request.query.lower(),  # Simple lowercase transformation
                limit=request.limit
            )
            results = basic_results
        
        # Limit to requested number of results
        results = results[:request.limit]
        
        logger.info(f"Search returned {len(results)} results")
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching articles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
        
@app.post("/topics", response_model=List[str])
async def search_topics(request: SearchRequest):
    """Search for topics similar to the query."""
    try:
        logger.info(f"Searching for topics with query: '{request.query}'")
        # Perform search
        topics = semantic_search.vector_db.search_topics(
            query=request.query,
            limit=request.limit
        )
        
        logger.info(f"Topic search returned {len(topics)} results")
        return topics
    except Exception as e:
        logger.error(f"Error searching topics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/articles/by-topic/{topic}", response_model=List[ArticleResponse])
async def get_articles_by_topic(topic: str, limit: int = 10):
    """Get articles with a specific topic."""
    try:
        logger.info(f"Getting articles with topic: '{topic}'")
        articles = vector_db.get_articles_by_topics([topic], limit=limit)
        
        logger.info(f"Found {len(articles)} articles with topic '{topic}'")
        return articles
    except Exception as e:
        logger.error(f"Error getting articles by topic: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/articles/similar/{article_id}", response_model=List[ArticleResponse])
async def get_similar_articles(article_id: str, limit: int = 5):
    """Get articles similar to the given article ID."""
    try:
        logger.info(f"Getting articles similar to '{article_id}'")
        articles = vector_db.get_similar_articles(article_id, limit=limit)
        
        logger.info(f"Found {len(articles)} similar articles")
        return articles
    except Exception as e:
        logger.error(f"Error getting similar articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))