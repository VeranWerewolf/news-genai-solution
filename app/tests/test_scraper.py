import pytest
from src.scraper.extractor import NewsExtractor
from unittest.mock import patch, MagicMock

def test_extract_from_url():
    extractor = NewsExtractor()
    url = "https://www.bbc.com/news/world-europe-56099778"
    
    # Test extraction
    article = extractor.extract_from_url(url)
    
    # Assert article properties
    assert article is not None
    assert 'url' in article
    assert 'title' in article
    assert 'text' in article
    assert len(article['text']) > 0

def test_trafilatura_extraction():
    """Test successful extraction with trafilatura."""
    with patch('trafilatura.fetch_url') as mock_fetch:
        with patch('trafilatura.extract') as mock_extract:
            extractor = NewsExtractor()
            
            # Setup mocks
            mock_fetch.return_value = "downloaded_content"
            mock_extract.return_value = '{"title": "Test Title", "text": "Test content", "author": "Test Author", "date": "2023-01-01"}'
            
            article = extractor.extract_from_url("https://example.com")
            
            # Verify results
            assert article is not None
            assert article['title'] == "Test Title"
            assert article['text'] == "Test content"
            assert article['authors'] == ["Test Author"]
            assert article['source'] == 'trafilatura'

def test_bs4_fallback():
    """Test fallback to BS4 when trafilatura fails."""
    with patch('trafilatura.fetch_url') as mock_fetch:
        with patch('requests.get') as mock_get:
            extractor = NewsExtractor()
            
            # Setup trafilatura to fail
            mock_fetch.return_value = None
            
            # Setup requests mock
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = """
            <html>
                <head><title>Test BS4 Title</title></head>
                <body>
                    <h1>Test Header</h1>
                    <article>
                        <p>Test paragraph 1.</p>
                        <p>Test paragraph 2.</p>
                    </article>
                    <div class="author">John Doe</div>
                    <time datetime="2023-01-01T12:00:00Z">Jan 1, 2023</time>
                </body>
            </html>
            """
            mock_get.return_value = mock_response
            
            article = extractor.extract_from_url("https://example.com")
            
            # Verify results
            assert article is not None
            assert article['title'] == "Test Header"  # It should pick h1 over title
            assert "Test paragraph 1." in article['text']
            assert "Test paragraph 2." in article['text']
            assert "John Doe" in article['authors']
            assert article['source'] == 'bs4'

def test_extraction_failure():
    """Test when both extraction methods fail."""
    with patch('trafilatura.fetch_url') as mock_fetch:
        with patch('requests.get') as mock_get:
            extractor = NewsExtractor()
            
            # Setup trafilatura to fail
            mock_fetch.return_value = None
            
            # Setup requests to fail
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