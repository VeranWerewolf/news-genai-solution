import newspaper
import trafilatura
from typing import Dict, Any, List, Optional


class NewsExtractor:
    """Module for extracting news content from URLs."""
    
    def __init__(self):
        """Initialize the news extractor."""
        pass
        
    def extract_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract news content from a given URL.
        
        Args:
            url: The URL of the news article to extract
            
        Returns:
            Dictionary containing article data or None if extraction failed
        """
        try:
            # Try extraction with trafilatura first
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                content = trafilatura.extract(downloaded, include_comments=False, 
                                             include_tables=True, output_format='json')
                if content:
                    import json
                    article_data = json.loads(content)
                    return {
                        'url': url,
                        'title': article_data.get('title', ''),
                        'text': article_data.get('text', ''),
                        'authors': article_data.get('author', ''),
                        'date': article_data.get('date', ''),
                        'source': 'trafilatura'
                    }
            
            # Fall back to newspaper3k if trafilatura fails
            article = newspaper.Article(url)
            article.download()
            article.parse()
            
            return {
                'url': url,
                'title': article.title,
                'text': article.text,
                'authors': article.authors,
                'date': article.publish_date,
                'source': 'newspaper3k'
            }
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return None
            
    def extract_from_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Extract content from multiple URLs.
        
        Args:
            urls: List of URLs to extract content from
            
        Returns:
            List of dictionaries containing article data
        """
        articles = []
        for url in urls:
            article = self.extract_from_url(url)
            if article:
                articles.append(article)
        
        return articles
