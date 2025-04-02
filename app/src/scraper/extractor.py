import trafilatura
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsExtractor:
    """Module for extracting news content from URLs."""
    
    def __init__(self):
        """Initialize the news extractor."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def _extract_with_bs4(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract article content using BeautifulSoup4 as a fallback method.
        
        Args:
            url: The URL of the news article
            
        Returns:
            Dictionary with article data or None if extraction failed
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}, status code: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = ""
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                title = title_tag.text.strip()
            
            # Extract content
            # Strategy 1: Look for article or main tags
            content_container = soup.find('article') or soup.find('main')
            
            # Strategy 2: If not found, look for common content div classes
            if not content_container:
                for div in soup.find_all('div', class_=re.compile(r'(content|article|story|body)', re.I)):
                    if len(div.get_text(strip=True)) > 200:  # Minimum content length
                        content_container = div
                        break
            
            # Strategy 3: If still not found, look for the div with most paragraphs
            if not content_container:
                max_p_count = 0
                for div in soup.find_all('div'):
                    p_count = len(div.find_all('p'))
                    if p_count > max_p_count:
                        max_p_count = p_count
                        content_container = div
            
            # Extract text from paragraphs
            paragraphs = []
            if content_container:
                for p in content_container.find_all('p'):
                    text = p.get_text().strip()
                    if len(text) > 20:  # Avoid empty or very short paragraphs
                        paragraphs.append(text)
            
            text = "\n\n".join(paragraphs)
            
            # Extract authors
            authors = []
            author_elements = soup.find_all(['span', 'div', 'a', 'p'], class_=re.compile(r'(author|byline)', re.I))
            for element in author_elements:
                author_text = element.get_text().strip()
                if author_text and len(author_text) < 100:  # Avoid getting entire sections
                    # Clean up common prefixes
                    author_text = re.sub(r'^(By|Author[s]?[:|\s])', '', author_text, flags=re.I).strip()
                    if author_text:
                        authors.append(author_text)
            
            # Extract date
            date = None
            # Look for time tags with datetime attribute
            time_tags = soup.find_all('time')
            for tag in time_tags:
                if tag.has_attr('datetime'):
                    date_str = tag['datetime']
                    try:
                        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        break
                    except ValueError:
                        continue
            
            # Look for meta tags with dates
            if not date:
                date_meta = soup.find('meta', property='article:published_time') or \
                           soup.find('meta', property='og:published_time') or \
                           soup.find('meta', itemprop='datePublished')
                if date_meta and date_meta.has_attr('content'):
                    try:
                        date = datetime.fromisoformat(date_meta['content'].replace('Z', '+00:00'))
                    except ValueError:
                        pass
            
            return {
                'url': url,
                'title': title,
                'text': text,
                'authors': authors,
                'date': date,
                'source': 'bs4'
            }
            
        except Exception as e:
            logger.error(f"Error in BS4 extraction for {url}: {e}")
            return None
        
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
                    article_data = json.loads(content)
                    return {
                        'url': url,
                        'title': article_data.get('title', ''),
                        'text': article_data.get('text', ''),
                        'authors': article_data.get('author', '').split(',') if article_data.get('author') else [],
                        'date': article_data.get('date', ''),
                        'source': 'trafilatura'
                    }
            
            # Fall back to BeautifulSoup if trafilatura fails
            return self._extract_with_bs4(url)
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
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