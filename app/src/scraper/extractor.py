import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsExtractor:
    """Module for extracting news content from URLs without trafilatura dependency."""
    
    def __init__(self):
        """Initialize the news extractor."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def extract_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract news content from a given URL using BeautifulSoup.
        
        Args:
            url: The URL of the news article to extract
            
        Returns:
            Dictionary containing article data or None if extraction failed
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}, status code: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title - prioritize h1 over title
            title = self._extract_title(soup)
            
            # Extract content
            text, content_container = self._extract_content(soup)
            
            # Extract authors
            authors = self._extract_authors(soup, content_container)
            
            # Extract date
            date = self._extract_date(soup)
            
            # Extract source (domain name)
            source = self._extract_source(url)
            
            # Only return if we have at least title and some text
            if title and text and len(text) > 100:  # Minimum content threshold
                return {
                    'url': url,
                    'title': title,
                    'text': text,
                    'authors': authors,
                    'date': date,
                    'source': source
                }
            else:
                logger.warning(f"Insufficient content extracted from {url}")
                return None
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the article title from the soup."""
        # Strategy 1: Look for h1 tags
        h1_tag = soup.find('h1')
        if h1_tag and len(h1_tag.get_text(strip=True)) > 5:
            return h1_tag.get_text(strip=True)
        
        # Strategy 2: Look for headline class/id
        headline_elements = soup.find_all(['h1', 'h2', 'div'], class_=re.compile(r'(headline|title)', re.I))
        headline_elements.extend(soup.find_all(['h1', 'h2', 'div'], id=re.compile(r'(headline|title)', re.I)))
        
        for element in headline_elements:
            text = element.get_text(strip=True)
            if text and len(text) > 5 and len(text) < 200:  # Reasonable title length
                return text
        
        # Strategy 3: Fall back to title tag
        title_tag = soup.find('title')
        if title_tag:
            # Often title tags include site name, try to clean it
            title_text = title_tag.get_text(strip=True)
            # Try to remove site name patterns like " - Site Name" or " | Site Name"
            site_name_separators = [' - ', ' | ', ' :: ', ' // ']
            for separator in site_name_separators:
                if separator in title_text:
                    return title_text.split(separator)[0].strip()
            return title_text
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> tuple[str, Optional[Any]]:
        """Extract the article content from the soup."""
        # Strategy 1: Look for article or main tags
        content_container = soup.find('article') or soup.find('main')
        
        # Strategy 2: Look for common content div classes/ids
        if not content_container:
            content_patterns = [
                r'(article|content|story|entry|post|text|body)',
                r'(news-article|article-body|story-content|entry-content|post-content)'
            ]
            
            for pattern in content_patterns:
                for element in soup.find_all(['div', 'section'], class_=re.compile(pattern, re.I)):
                    if len(element.get_text(strip=True)) > 200:  # Minimum content length
                        content_container = element
                        break
                        
                if content_container:
                    break
                    
                # Try with ID attributes
                for element in soup.find_all(['div', 'section'], id=re.compile(pattern, re.I)):
                    if len(element.get_text(strip=True)) > 200:
                        content_container = element
                        break
                        
                if content_container:
                    break
        
        # Strategy 3: If still not found, look for the div with most paragraphs
        if not content_container:
            max_p_count = 0
            candidate_container = None
            
            for div in soup.find_all(['div', 'section']):
                paragraphs = div.find_all('p')
                p_count = len(paragraphs)
                p_text_length = sum(len(p.get_text(strip=True)) for p in paragraphs)
                
                # Prioritize both paragraph count and text length
                if p_count > 3 and p_text_length > max_p_count:
                    max_p_count = p_text_length
                    candidate_container = div
            
            content_container = candidate_container
        
        # Extract text from paragraphs
        if content_container:
            # Find all paragraphs that are likely to be content (not nav, ads, etc.)
            paragraphs = []
            for p in content_container.find_all('p'):
                # Skip paragraphs that are likely to be navigation, ads, etc.
                if any(cls in str(p.get('class', [])).lower() for cls in ['nav', 'menu', 'copyright', 'footer', 'ad']):
                    continue
                
                text = p.get_text().strip()
                if len(text) > 20:  # Avoid empty or very short paragraphs
                    paragraphs.append(text)
            
            # If we didn't find good paragraphs, try direct text
            if not paragraphs:
                text = content_container.get_text().strip()
                # Split into pseudo-paragraphs to clean up
                text_parts = re.split(r'\n\s*\n', text)
                paragraphs = [part.strip() for part in text_parts if len(part.strip()) > 20]
            
            text = "\n\n".join(paragraphs)
        else:
            # Last resort: Try to find any div with substantial text
            all_text = soup.get_text()
            text_chunks = re.split(r'\n\s*\n', all_text)
            paragraphs = [chunk.strip() for chunk in text_chunks if len(chunk.strip()) > 40]
            text = "\n\n".join(paragraphs)
            
        return text, content_container
    
    def _extract_authors(self, soup: BeautifulSoup, content_container: Optional[Any]) -> List[str]:
        """Extract the article authors from the soup."""
        authors = []
        
        # Strategy 1: Look for common author class/id patterns
        author_patterns = [
            r'(author|byline|writer|contributor)',
            r'(meta-author|article-author|story-author)'
        ]
        
        for pattern in author_patterns:
            author_elements = soup.find_all(['span', 'div', 'a', 'p'], class_=re.compile(pattern, re.I))
            author_elements.extend(soup.find_all(['span', 'div', 'a', 'p'], id=re.compile(pattern, re.I)))
            
            for element in author_elements:
                author_text = element.get_text().strip()
                if author_text and len(author_text) < 100:  # Avoid getting entire sections
                    # Clean up common prefixes
                    author_text = re.sub(r'^(By|Author[s]?[:|\s])', '', author_text, flags=re.I).strip()
                    if author_text and author_text not in authors:
                        authors.append(author_text)
        
        # Strategy 2: Look for schema.org author markup
        schema_authors = soup.find_all(['span', 'div', 'a'], itemprop='author')
        for author in schema_authors:
            author_text = author.get_text().strip()
            if author_text and author_text not in authors:
                authors.append(author_text)
        
        # Strategy 3: Look for rel="author" links
        rel_authors = soup.find_all('a', rel='author')
        for author in rel_authors:
            author_text = author.get_text().strip()
            if author_text and author_text not in authors:
                authors.append(author_text)
        
        # Cleanup authors list
        clean_authors = []
        for author in authors:
            # Remove excessive whitespace
            author = re.sub(r'\s+', ' ', author).strip()
            # Remove "By" prefix if present
            if author.lower().startswith('by '):
                author = author[3:].strip()
            # Make sure it's reasonable length for an author name
            if len(author) > 2 and len(author) < 50:
                clean_authors.append(author)
        
        return clean_authors
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract the article publication date from the soup."""
        # Strategy 1: Look for time tags with datetime attribute
        time_tags = soup.find_all('time')
        for tag in time_tags:
            if tag.has_attr('datetime'):
                date_str = tag['datetime']
                try:
                    # Handle ISO format with timezone
                    if 'T' in date_str and ('+' in date_str or 'Z' in date_str):
                        date_str = date_str.replace('Z', '+00:00')
                        return datetime.fromisoformat(date_str)
                    # Handle just date format like 2023-04-23
                    elif re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                        return datetime.fromisoformat(date_str)
                except ValueError:
                    continue
        
        # Strategy 2: Look for meta tags with dates
        date_metas = [
            soup.find('meta', property='article:published_time'),
            soup.find('meta', property='og:published_time'),
            soup.find('meta', itemprop='datePublished'),
            soup.find('meta', name='pubdate'),
            soup.find('meta', name='publishdate'),
            soup.find('meta', name='timestamp')
        ]
        
        for meta in date_metas:
            if meta and meta.has_attr('content'):
                try:
                    date_str = meta['content']
                    if 'T' in date_str and ('+' in date_str or 'Z' in date_str):
                        date_str = date_str.replace('Z', '+00:00')
                    return datetime.fromisoformat(date_str)
                except ValueError:
                    continue
        
        # Strategy 3: Look for dates in text with common formats
        date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,.\s]+\d{1,2}(?:st|nd|rd|th)?[,.\s]+\d{4}\b'
        date_matches = re.findall(date_pattern, soup.get_text(), re.I)
        
        if date_matches:
            # Try to parse found dates (this is simplistic, could be improved)
            for date_text in date_matches:
                try:
                    # Format might vary, so let's clean it
                    date_text = re.sub(r'(st|nd|rd|th)', '', date_text)
                    # Try multiple formats
                    for fmt in ['%B %d, %Y', '%B %d %Y', '%b %d, %Y', '%b %d %Y']:
                        try:
                            return datetime.strptime(date_text, fmt)
                        except ValueError:
                            continue
                except Exception:
                    continue
        
        return None
    
    def _extract_source(self, url: str) -> str:
        """Extract the source (domain name) from the URL."""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            # Remove www. if present
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return ""
    
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
            try:
                article = self.extract_from_url(url)
                if article:
                    articles.append(article)
                else:
                    logger.warning(f"No content extracted from {url}")
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
        
        return articles