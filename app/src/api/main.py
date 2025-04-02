from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional

from ..scraper.extractor import NewsExtractor
from ..genai.analyzer import ArticleAnalyzer
from ..database.vector_store import VectorDatabase
from ..search.semantic_search import SemanticSearch

app = FastAPI(
    title="News GenAI API",
    description="API for news extraction, analysis, and semantic search",
    version="1.0.0"
)

# Create instances of components
news_extractor = NewsExtractor()
article_analyzer = ArticleAnalyzer()
vector_db = VectorDatabase()
semantic_search = SemanticSearch()

# Define request and response models
class UrlListRequest(BaseModel):
    urls: List[HttpUrl]

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

@app.post("/extract", response_model=List[ArticleResponse])
async def extract_articles(request: UrlListRequest):
    """Extract articles from the provided URLs."""
    try:
        # Extract articles
        articles = news_extractor.extract_from_urls(request.urls)
        if not articles:
            raise HTTPException(status_code=404, detail="No articles could be extracted")
            
        return articles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=List[ArticleResponse])
async def analyze_articles(request: UrlListRequest):
    """Extract and analyze articles from the provided URLs."""
    try:
        # Extract articles
        articles = news_extractor.extract_from_urls(request.urls)
        if not articles:
            raise HTTPException(status_code=404, detail="No articles could be extracted")
            
        # Analyze articles
        analyzed_articles = article_analyzer.analyze_articles(articles)
            
        return analyzed_articles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/store", response_model=List[str])
async def store_articles(request: UrlListRequest):
    """Extract, analyze, and store articles from the provided URLs."""
    try:
        # Extract articles
        articles = news_extractor.extract_from_urls(request.urls)
        if not articles:
            raise HTTPException(status_code=404, detail="No articles could be extracted")
            
        # Analyze articles
        analyzed_articles = article_analyzer.analyze_articles(articles)
        
        # Store articles
        article_ids = vector_db.store_articles(analyzed_articles)
            
        return article_ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=List[ArticleResponse])
async def search_articles(request: SearchRequest):
    """Search for articles matching the query."""
    try:
        # Perform search
        results = semantic_search.search(
            query=request.query,
            enhance=request.enhance,
            limit=request.limit
        )
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
