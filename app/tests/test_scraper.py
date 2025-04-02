import pytest
from src.scraper.extractor import NewsExtractor
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

def test_extract_from_url():
    """Test basic extraction functionality."""
    with patch('requests.get') as mock_get:
        extractor = NewsExtractor()
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = """
        <html>
            <head><title>Test Article - News Site</title></head>
            <body>
                <h1>Test Headline</h1>
                <div class="article-content">
                    <p>This is test paragraph 1.</p>
                    <p>This is test paragraph 2.</p>
                </div>
                <div class="author">Test Author</div>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        # Test extraction
        article = extractor.extract_from_url("https://example.com")
        
        # Assert article properties
        assert article is not None
        assert article['url'] == "https://example.com"
        assert article['title'] == "Test Headline"
        assert "This is test paragraph 1." in article['text']
        assert "This is test paragraph 2." in article['text']
        assert "Test Author" in article['authors']

def test_extract_title():
    """Test title extraction logic."""
    extractor = NewsExtractor()
    
    # Test with h1
    html = "<html><body><h1>Main Headline</h1></body></html>"
    soup = BeautifulSoup(html, 'html.parser')
    assert extractor._extract_title(soup) == "Main Headline"
    
    # Test with title class
    html = '<html><body><div class="headline">Class Headline</div></body></html>'
    soup = BeautifulSoup(html, 'html.parser')
    assert extractor._extract_title(soup) == "Class Headline"
    
    # Test with title tag and site name
    html = "<html><head><title>Page Title - Site Name</title></head></html>"
    soup = BeautifulSoup(html, 'html.parser')
    assert extractor._extract_title(soup) == "Page Title"

def test_extract_content():
    """Test content extraction logic."""
    extractor = NewsExtractor()
    
    # Test with article tag
    html = """
    <html><body>
        <article>
            <p>Article paragraph 1.</p>
            <p>Article paragraph 2.</p>
        </article>
    </body></html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    text, container = extractor._extract_content(soup)
    assert "Article paragraph 1." in text
    assert "Article paragraph 2." in text
    
    # Test with content class
    html = """
    <html><body>
        <div class="content">
            <p>Content paragraph 1.</p>
            <p>Content paragraph 2.</p>
        </div>
    </body></html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    text, container = extractor._extract_content(soup)
    assert "Content paragraph 1." in text
    assert "Content paragraph 2." in text

def test_extract_authors():
    """Test author extraction logic."""
    extractor = NewsExtractor()
    
    # Test with author class
    html = """
    <html><body>
        <span class="author">John Smith</span>
    </body></html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    authors = extractor._extract_authors(soup, None)
    assert "John Smith" in authors
    
    # Test with byline and "By" prefix
    html = """
    <html><body>
        <div class="byline">By Jane Doe</div>
    </body></html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    authors = extractor._extract_authors(soup, None)
    assert "Jane Doe" in authors
    
    # Test with schema.org markup
    html = """
    <html><body>
        <span itemprop="author">Mark Johnson</span>
    </body></html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    authors = extractor._extract_authors(soup, None)
    assert "Mark Johnson" in authors

def test_extract_date():
    """Test date extraction logic."""
    extractor = NewsExtractor()
    
    # Test with time tag
    html = """
    <html><body>
        <time datetime="2025-04-01T10:30:00Z">April 1, 2025</time>
    </body></html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    date = extractor._extract_date(soup)
    assert date is not None
    assert date.year == 2025
    assert date.month == 4
    assert date.day == 1
    
    # Test with meta tag
    html = """
    <html><head>
        <meta property="article:published_time" content="2025-03-15T08:45:00Z">
    </head></html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    date = extractor._extract_date(soup)
    assert date is not None
    assert date.year == 2025
    assert date.month == 3
    assert date.day == 15

def test_extract_source():
    """Test source extraction logic."""
    extractor = NewsExtractor()
    
    # Test with www prefix
    assert extractor._extract_source("https://www.example.com/article") == "example.com"
    
    # Test without www prefix
    assert extractor._extract_source("https://news.example.org/story/12345") == "news.example.org"
    
    # Test with subdomain
    assert extractor._extract_source("https://politics.news.example.net/2025/04/01/headline") == "politics.news.example.net"

def test_extraction_failure():
    """Test when extraction fails."""
    with patch('requests.get') as mock_get:
        extractor = NewsExtractor()
        
        # Setup request to fail
        mock_get.side_effect = Exception("Connection error")
        
        article = extractor.extract_from_url("https://example.com")
        
        # Verify results
        assert article is None

def test_extract_from_urls():
    """Test extracting from multiple URLs."""
    with patch.object(NewsExtractor, 'extract_from_url') as mock_extract:
        extractor = NewsExtractor()
        
        # Setup mock to return different results for different URLs
        def side_effect(url):
            if url == "https://example.com/1":
                return {"url": url, "title": "Article 1", "text": "Content 1"}
            elif url == "https://example.com/2":
                return {"url": url, "title": "Article 2", "text": "Content 2"}
            elif url == "https://example.com/3":
                return None  # Simulate failure
            return None
        
        mock_extract.side_effect = side_effect
        
        urls = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3"
        ]
        
        articles = extractor.extract_from_urls(urls)
        
        # Verify results
        assert len(articles) == 2  # Only successful extractions should be included
        assert articles[0]["title"] == "Article 1"
        assert articles[1]["title"] == "Article 2"