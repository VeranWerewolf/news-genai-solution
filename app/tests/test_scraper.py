import pytest
from src.scraper.extractor import NewsExtractor

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
