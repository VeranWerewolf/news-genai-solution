from typing import Dict, Any, List, Optional, Tuple
import os
import uuid
import hashlib
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from langchain.vectorstores import Chroma

# Import local embeddings
from ..genai.embeddings import LocalSentenceTransformerEmbeddings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDatabase:
    """Interface for storing and retrieving vectorized article data."""
    
    def __init__(self, db_type: str = "qdrant"):
        """
        Initialize the vector database.
        
        Args:
            db_type: Type of vector database to use ('qdrant' or 'chroma')
        """
        self.db_type = db_type
        # Use local sentence transformer embeddings
        self.embeddings = LocalSentenceTransformerEmbeddings()
        
        # Define embedding dimensions based on the model
        self.embedding_dim = 384  # Default dimension for all-MiniLM-L6-v2
        
        if db_type == "qdrant":
            # Initialize Qdrant client
            self.client = QdrantClient(
                host=os.getenv("VECTOR_DB_HOST", "vector-db"),
                port=int(os.getenv("VECTOR_DB_PORT", 6333))
            )
            
            # Create collections if they don't exist
            self.collections = {
                "news_articles": {
                    "size": self.embedding_dim,  # Sentence transformer embedding dimension
                    "distance": models.Distance.COSINE
                },
                "news_topics": {
                    "size": self.embedding_dim,
                    "distance": models.Distance.COSINE
                }
            }
            
            self._initialize_collections()
        
        elif db_type == "chroma":
            # Initialize ChromaDB
            self.db = Chroma(
                collection_name="news_articles",
                embedding_function=self.embeddings,
                persist_directory="./data/chroma"
            )
    
    def _initialize_collections(self):
        """Initialize Qdrant collections if they don't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            for name, config in self.collections.items():
                if name not in collection_names:
                    logger.info(f"Creating collection {name}")
                    self.client.create_collection(
                        collection_name=name,
                        vectors_config=models.VectorParams(
                            size=config["size"],
                            distance=config["distance"]
                        ),
                        optimizers_config=models.OptimizersConfigDiff(
                            indexing_threshold=20000,  # Larger threshold for better performance
                            memmap_threshold=20000
                        ),
                        hnsw_config=models.HnswConfigDiff(
                            m=16,  # Higher for better recall, but slower indexing
                            ef_construct=100,  # Higher for better recall
                            full_scan_threshold=10000  # Threshold to switch to brute force
                        )
                    )
        except Exception as e:
            logger.error(f"Error initializing collections: {e}")
            raise
    
    def _get_article_id(self, article: Dict[str, Any]) -> str:
        """
        Generate a consistent ID for an article.
        
        Args:
            article: Article data dictionary
            
        Returns:
            Article ID
        """
        # Use URL if available
        if 'url' in article and article['url']:
            # Hash the URL to create a valid ID
            return hashlib.md5(article['url'].encode()).hexdigest()
        
        # Otherwise use title
        if 'title' in article and article['title']:
            return hashlib.md5(article['title'].encode()).hexdigest()
            
        # Last resort, generate a random ID
        return str(uuid.uuid4())
    
    def store_article(self, article: Dict[str, Any]) -> str:
        """
        Store an article in the vector database.
        
        Args:
            article: Article data dictionary with 'summary' and 'topics'
            
        Returns:
            ID of the stored article
        """
        # Generate article ID
        article_id = self._get_article_id(article)
        
        # Create a combined text for embedding
        combined_text = f"{article['title']} {article['summary']} {' '.join(article['topics'])}"
        
        try:
            if self.db_type == "qdrant":
                # Get embedding
                embedding = self.embeddings.embed_query(combined_text)
                
                # Create full payload with all article metadata
                payload = {
                    'id': article_id,
                    'title': article.get('title', ''),
                    'summary': article.get('summary', ''),
                    'text': article.get('text', ''),
                    'topics': article.get('topics', []),
                    'url': article.get('url', ''),
                    'source': article.get('source', ''),
                    'authors': article.get('authors', []),
                    'date': str(article.get('date', '')),
                    'created_at': article.get('created_at', ''),
                    'updated_at': article.get('updated_at', '')
                }
                
                # Store in Qdrant
                self.client.upsert(
                    collection_name="news_articles",
                    points=[
                        models.PointStruct(
                            id=article_id,
                            vector=embedding,
                            payload=payload
                        )
                    ]
                )
                
                # Store topic embeddings separately
                if 'topics' in article and article['topics']:
                    for topic in article['topics']:
                        topic_embedding = self.embeddings.embed_query(topic)
                        topic_id = hashlib.md5(topic.encode()).hexdigest()
                        
                        # Check if topic already exists
                        try:
                            existing_topic = self.client.retrieve(
                                collection_name="news_topics",
                                ids=[topic_id]
                            )
                            
                            if existing_topic:
                                # Update existing topic with new article reference
                                existing_articles = existing_topic[0].payload.get('articles', [])
                                if article_id not in existing_articles:
                                    existing_articles.append(article_id)
                                    
                                self.client.upsert(
                                    collection_name="news_topics",
                                    points=[
                                        models.PointStruct(
                                            id=topic_id,
                                            vector=topic_embedding,
                                            payload={
                                                'topic': topic,
                                                'articles': existing_articles
                                            }
                                        )
                                    ]
                                )
                            else:
                                # Create new topic
                                self.client.upsert(
                                    collection_name="news_topics",
                                    points=[
                                        models.PointStruct(
                                            id=topic_id,
                                            vector=topic_embedding,
                                            payload={
                                                'topic': topic,
                                                'articles': [article_id]
                                            }
                                        )
                                    ]
                                )
                        except Exception as e:
                            # Create new topic if retrieval fails
                            logger.warning(f"Error retrieving topic, creating new: {e}")
                            self.client.upsert(
                                collection_name="news_topics",
                                points=[
                                    models.PointStruct(
                                        id=topic_id,
                                        vector=topic_embedding,
                                        payload={
                                            'topic': topic,
                                            'articles': [article_id]
                                        }
                                    )
                                ]
                            )
                
            elif self.db_type == "chroma":
                # Store in ChromaDB
                ids = self.db.add_texts(
                    texts=[combined_text],
                    metadatas=[article],
                    ids=[article_id]
                )
                
            return article_id
            
        except Exception as e:
            logger.error(f"Error storing article: {e}")
            raise
    
    def store_articles(self, articles: List[Dict[str, Any]]) -> List[str]:
        """
        Store multiple articles in the vector database.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            List of stored article IDs
        """
        article_ids = []
        for article in articles:
            article_id = self.store_article(article)
            article_ids.append(article_id)
            
        return article_ids
    
    def update_article_topic(self, article_id: str, topics: List[str]) -> bool:
        """
        Update the topics for an existing article.
        
        Args:
            article_id: ID of the article
            topics: New list of topics
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.db_type == "qdrant":
                # Get the article
                results = self.client.retrieve(
                    collection_name="news_articles",
                    ids=[article_id]
                )
                
                if not results:
                    return False
                    
                article = results[0].payload
                article['topics'] = topics
                
                # Update in Qdrant
                self.client.upsert(
                    collection_name="news_articles",
                    points=[
                        models.PointStruct(
                            id=article_id,
                            vector=self.embeddings.embed_query(
                                f"{article['title']} {article.get('summary', '')} {' '.join(topics)}"
                            ),
                            payload=article
                        )
                    ]
                )
                
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error updating article topics: {e}")
            return False
    
    def search(self, query: str, limit: int = 5, filter_by_topics: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for articles similar to the query with multiple search strategies.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            filter_by_topics: Optional list of topics to filter results
            
        Returns:
            List of articles matching the query
        """
        try:
            if self.db_type == "qdrant":
                all_results = []
                
                # Strategy 1: Vector similarity search
                try:
                    # Get embedding for query
                    query_embedding = self.embeddings.embed_query(query)
                    
                    # Create filter if topics provided
                    search_filter = None
                    if filter_by_topics:
                        search_filter = models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="topics",
                                    match=models.MatchAny(any=filter_by_topics)
                                )
                            ]
                        )
                    
                    # Search in Qdrant
                    search_params = {
                        "collection_name": "news_articles",
                        "query_vector": query_embedding,
                        "limit": limit,
                        "score_threshold": 0.5  # Set a relevance threshold
                    }
                    
                    # Only add filter if it exists
                    if search_filter is not None:
                        search_params["filter"] = search_filter
                    
                    vector_results = self.client.search(**search_params)
                    
                    # Extract articles from results
                    all_results.extend([point.payload for point in vector_results])
                    logger.info(f"Vector search for '{query}' found {len(vector_results)} results")
                except Exception as e:
                    logger.error(f"Vector search failed: {e}")
                
                # Strategy 2: Keyword matching fallback if we don't have enough results
                if len(all_results) < limit:
                    try:
                        logger.info(f"Trying keyword fallback for '{query}'")
                        
                        # Prepare filter conditions
                        filter_conditions = []
                        
                        # Add topic filter if provided
                        if filter_by_topics:
                            filter_conditions.append(
                                models.FieldCondition(
                                    key="topics",
                                    match=models.MatchAny(any=filter_by_topics)
                                )
                            )
                        
                        # Text search conditions
                        text_conditions = []
                        
                        # Search in title with full query
                        text_conditions.append(
                            models.FieldCondition(
                                key="title", 
                                match=models.MatchText(text=query)
                            )
                        )
                        
                        # Search in summary with full query
                        text_conditions.append(
                            models.FieldCondition(
                                key="summary", 
                                match=models.MatchText(text=query)
                            )
                        )
                        
                        # Also search by individual keywords for broader matches
                        keywords = [k.strip() for k in query.lower().split() if len(k.strip()) > 3]
                        for keyword in keywords:
                            # Search in title with keyword
                            text_conditions.append(
                                models.FieldCondition(
                                    key="title", 
                                    match=models.MatchText(text=keyword)
                                )
                            )
                            
                            # Search in summary with keyword
                            text_conditions.append(
                                models.FieldCondition(
                                    key="summary", 
                                    match=models.MatchText(text=keyword)
                                )
                            )
                            
                            # Search in topics with keyword
                            text_conditions.append(
                                models.FieldCondition(
                                    key="topics", 
                                    match=models.MatchText(text=keyword)
                                )
                            )
                        
                        # Any text match is acceptable
                        if text_conditions:
                            filter_conditions.append(
                                models.Filter(
                                    should=text_conditions
                                )
                            )
                        
                        # Only perform search if we have filter conditions
                        if filter_conditions:
                            combined_filter = None
                            if len(filter_conditions) > 1:
                                combined_filter = models.Filter(
                                    must=filter_conditions
                                )
                            else:
                                combined_filter = filter_conditions[0]
                            
                            # Perform the keyword search - FIX: Use scroll with filter properly
                            # The error is in using 'filter' parameter - it should be passed directly, not as a named parameter
                            scroll_results = self.client.scroll(
                                collection_name="news_articles",
                                limit=limit,
                                with_payload=True,
                                with_vectors=False,
                                filter=combined_filter  # This is correct, pass the filter directly
                            )
                            
                            # Extract articles from results
                            if scroll_results and scroll_results[0]:
                                keyword_articles = [point.payload for point in scroll_results[0]]
                                logger.info(f"Keyword search found {len(keyword_articles)} results")
                                
                                # Add only new, non-duplicate results
                                existing_ids = {article.get('id') for article in all_results}
                                for article in keyword_articles:
                                    if article.get('id') not in existing_ids:
                                        all_results.append(article)
                                        existing_ids.add(article.get('id'))
                    except Exception as e:
                        logger.error(f"Keyword fallback search failed: {e}")
                
                # Return results, limited to requested count
                return all_results[:limit]
                
            elif self.db_type == "chroma":
                # Search in ChromaDB
                results = self.db.similarity_search_with_relevance_scores(
                    query,
                    k=limit
                )
                
                # Extract articles from results
                articles = [doc.metadata for doc, _ in results]
                
                # Filter by topics if provided
                if filter_by_topics:
                    articles = [
                        article for article in articles
                        if any(topic in article.get('topics', []) for topic in filter_by_topics)
                    ]
                
                return articles
                
        except Exception as e:
            logger.error(f"Error searching articles: {e}")
            return []
    
    def search_topics(self, query: str, limit: int = 5) -> List[str]:
        """
        Search for topics similar to the query.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of topics matching the query
        """
        try:
            if self.db_type == "qdrant":
                # Get embedding for query
                query_embedding = self.embeddings.embed_query(query)
                
                # Search in Qdrant
                results = self.client.search(
                    collection_name="news_topics",
                    query_vector=query_embedding,
                    limit=limit
                )
                
                # Extract topics from results
                topics = [point.payload.get('topic') for point in results]
                return topics
            
            return []
            
        except Exception as e:
            logger.error(f"Error searching topics: {e}")
            return []
    
    def get_similar_articles(self, article_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get articles similar to the given article.
        
        Args:
            article_id: ID of the reference article
            limit: Maximum number of results to return
            
        Returns:
            List of similar articles
        """
        try:
            if self.db_type == "qdrant":
                # Get the article
                results = self.client.retrieve(
                    collection_name="news_articles",
                    ids=[article_id]
                )
                
                if not results:
                    return []
                
                # Get similar articles
                similar = self.client.search(
                    collection_name="news_articles",
                    query_vector=results[0].vector,
                    limit=limit + 1  # +1 because the article itself will be included
                )
                
                # Filter out the query article
                articles = [
                    point.payload for point in similar
                    if point.id != article_id
                ]
                
                return articles[:limit]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting similar articles: {e}")
            return []
            
    def get_articles_by_topics(self, topics: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get articles that have the specified topics.
        
        Args:
            topics: List of topic names
            limit: Maximum number of articles to return
            
        Returns:
            List of article dictionaries
        """
        try:
            if self.db_type == "qdrant":
                # For Qdrant, there are two approaches to try:
                # 1. First try using the search method with a filter
                try:
                    # Create filter for topics
                    search_filter = models.Filter(
                        must=[
                            models.FieldCondition(
                                key="topics",
                                match=models.MatchAny(any=topics)
                            )
                        ]
                    )
                    
                    # Use search with a null vector but with filter
                    # This is sometimes called a "filter-only" search
                    null_vector = [0.0] * self.embedding_dim  # Zero vector for pure filter search
                    
                    search_results = self.client.search(
                        collection_name="news_articles",
                        query_vector=null_vector,
                        query_filter=search_filter,
                        limit=limit,
                        with_payload=True,
                        score_threshold=None  # Don't use score threshold for filter-only search
                    )
                    
                    # Extract articles from results
                    if search_results:
                        articles = [point.payload for point in search_results]
                        logger.info(f"Found {len(articles)} articles using topic filter search")
                        return articles
                except Exception as e:
                    logger.warning(f"Filter search failed, trying alternate method: {e}")
                
                # 2. If the first approach fails, try using the scroll method correctly
                try:
                    # The scroll method requires a filter_selector field not just filter
                    scroll_results = self.client.scroll(
                        collection_name="news_articles",
                        limit=limit,
                        with_payload=True,
                        with_vectors=False,
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="topics",
                                    match=models.MatchAny(any=topics)
                                )
                            ]
                        )
                    )
                    
                    # Extract articles from results
                    if scroll_results and scroll_results[0]:
                        articles = [point.payload for point in scroll_results[0]]
                        logger.info(f"Found {len(articles)} articles using topic filter scroll")
                        return articles
                except Exception as e:
                    logger.warning(f"Scroll method with filter failed: {e}")
                
                # 3. Last resort: Get topic-associated article IDs and retrieve them
                try:
                    all_article_ids = set()
                    
                    # Look up each topic separately to find associated articles
                    for topic in topics:
                        # Hash the topic name to get its ID
                        topic_id = hashlib.md5(topic.encode()).hexdigest()
                        
                        # Try retrieving the topic
                        topic_results = self.client.retrieve(
                            collection_name="news_topics",
                            ids=[topic_id],
                            with_payload=True
                        )
                        
                        if topic_results:
                            # Get article IDs associated with this topic
                            article_ids = topic_results[0].payload.get('articles', [])
                            for article_id in article_ids:
                                all_article_ids.add(article_id)
                    
                    # If we found article IDs, retrieve them
                    if all_article_ids:
                        # Convert to list and limit
                        article_ids_list = list(all_article_ids)[:limit]
                        
                        # Retrieve articles
                        articles = []
                        for article_id in article_ids_list:
                            article_result = self.client.retrieve(
                                collection_name="news_articles",
                                ids=[article_id],
                                with_payload=True
                            )
                            
                            if article_result:
                                articles.append(article_result[0].payload)
                        
                        logger.info(f"Found {len(articles)} articles using topic-article mapping")
                        return articles
                except Exception as e:
                    logger.error(f"All topic search methods failed: {e}")
                
                # If all methods failed
                return []
                
            return []
            
        except Exception as e:
            logger.error(f"Error getting articles by topics: {e}")
            return []