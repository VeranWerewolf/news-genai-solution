from typing import Dict, Any, List, Set
import os
import logging
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from sentence_transformers import SentenceTransformer

from ..database.vector_store import VectorDatabase
from ..genai.llm_client import OllamaLLM, OllamaChat

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticSearch:
    """Provides semantic search capabilities for news articles."""
    
    def __init__(self, model_name: str = "llama3"):
        """Initialize the semantic search engine.
        
        Args:
            model_name: Name of the Ollama model to use
        """
        # Initialize the Ollama LLM
        try:
            self.llm = OllamaLLM(model_name=model_name, temperature=0.0)
            logger.info(f"Initialized OllamaLLM with model {model_name} for semantic search")
        except Exception as e:
            logger.error(f"Failed to initialize OllamaLLM for semantic search: {e}")
            # Fallback to direct implementation
            self.llm = OllamaChat(model_name=model_name, temperature=0.0)
            logger.info(f"Fallback to OllamaChat with model {model_name} for semantic search")
            
        self.vector_db = VectorDatabase()
        
        # Initialize sentence transformer for embeddings
        try:
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Initialized sentence transformer model")
        except Exception as e:
            logger.error(f"Failed to initialize sentence transformer: {e}")
            self.sentence_transformer = None
        
        # Create prompt for query enhancement
        self.query_enhancement_prompt = PromptTemplate(
            input_variables=["query"],
            template="""
            Original search query: {query}
            
            Rewrite this search query to improve semantic search results for news articles.
            Add relevant synonyms and related terms that would help find matching content.
            Your response should be ONLY the improved search query with no explanations or additional text.
            Make sure to include the key terms from the original query.
            """
        )
        
        # Create chain for query enhancement
        self.query_chain = LLMChain(llm=self.llm, prompt=self.query_enhancement_prompt)
        
    def enhance_query(self, query: str) -> str:
        """
        Enhance the search query using AI to improve search results.
        
        Args:
            query: Original search query
            
        Returns:
            Enhanced search query
        """
        try:
            enhanced_query = self.query_chain.run(query=query)
            enhanced = enhanced_query.strip()
            if enhanced:
                return enhanced
            return query
        except Exception as e:
            logger.error(f"Error enhancing query: {e}")
            return query  # Return original query if enhancement fails
    
    def expand_query_with_synonyms(self, query: str) -> List[str]:
        """
        Expand the query with synonyms and related terms using the LLM.
        
        Args:
            query: Original search query
            
        Returns:
            List of expanded query terms
        """
        try:
            # Create a prompt for synonym generation
            prompt = f"""
            Generate 5-8 synonyms or closely related terms for: "{query}"
            
            Focus on terms that would be useful for searching news articles.
            Include both broader and more specific related concepts.
            Respond ONLY with the terms, one per line, without numbering or explanation.
            """
            
            # Generate synonyms
            synonyms_text = self.llm(prompt)
            
            # Process the response
            synonyms = [term.strip() for term in synonyms_text.split('\n') if term.strip()]
            
            # Add original query as first term
            all_terms = [query] + synonyms
            
            # Remove duplicates and empty strings
            unique_terms = list(dict.fromkeys([term for term in all_terms if term]))
            
            logger.info(f"Expanded query '{query}' to {len(unique_terms)} terms: {unique_terms}")
            return unique_terms
            
        except Exception as e:
            logger.error(f"Error expanding query with synonyms: {e}")
            # As fallback, generate some basic variations
            variants = [
                query,
                query.lower(),
                query.title(),
                # Add plural/singular variations for simple cases
                f"{query}s" if not query.endswith('s') else query[:-1],
            ]
            return list(set(variants))

    def get_related_topics(self, query: str, limit: int = 3) -> List[str]:
        """
        Get topics related to the search query.
        
        Args:
            query: Search query
            limit: Maximum number of topics to return
            
        Returns:
            List of related topics
        """
        try:
            # Get related topics from vector DB
            topics = self.vector_db.search_topics(query, limit=limit)
            if topics:
                logger.info(f"Found related topics for '{query}': {topics}")
                return topics
            return []
        except Exception as e:
            logger.error(f"Error getting related topics: {e}")
            return []
            
    def search(self, query: str, enhance: bool = True, limit: int = 5, filter_by_topics: List[str] = None) -> List[Dict[str, Any]]:
        """
        Perform semantic search for news articles using multiple strategies.
        
        Args:
            query: Search query
            enhance: Whether to enhance the query using AI
            limit: Maximum number of results to return
            filter_by_topics: Optional list of topics to filter results
            
        Returns:
            List of matching articles
        """
        if not query or query.strip() == "":
            logger.warning("Empty search query provided")
            return []
            
        try:
            all_results = []
            seen_ids = set()
            
            # Strategy 1: Direct search with original query
            logger.info(f"Strategy 1: Direct search with original query: '{query}'")
            direct_results = self.vector_db.search(query, limit=limit, filter_by_topics=filter_by_topics)
            self._add_unique_results(direct_results, all_results, seen_ids)
            
            # If we already have enough results and don't need to enhance, return early
            if len(all_results) >= limit and not enhance:
                return all_results[:limit]
            
            # Strategy 2: Topic-based discovery (if requested)
            if enhance:
                if len(all_results) < limit:
                    related_topics = self.get_related_topics(query, limit=3)
                    if related_topics and not filter_by_topics:
                        logger.info(f"Strategy 4: Topic-based discovery with topics: {related_topics}")
                        topic_results = self.vector_db.get_articles_by_topics(related_topics, limit=limit)
                        self._add_unique_results(topic_results, all_results, seen_ids)
            
            # Log search results
            logger.info(f"Search for '{query}' returned {len(all_results)} results after all strategies")
            
            # Return limited results
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            # Last resort fallback - try direct search with minimal processing
            try:
                return self.vector_db.search(query.lower(), limit=limit, filter_by_topics=filter_by_topics)
            except Exception:
                return []  # Return empty list if all methods fail
    
    def _add_unique_results(self, new_results: List[Dict[str, Any]], all_results: List[Dict[str, Any]], seen_ids: Set[str]):
        """
        Helper method to add unique results to the aggregated results list.
        
        Args:
            new_results: New results to add
            all_results: Existing aggregated results
            seen_ids: Set of already seen article IDs
        """
        for result in new_results:
            # Get a unique identifier for the result
            result_id = result.get('id') or result.get('url')
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                all_results.append(result)
    
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
            # Direct topic search
            topics = self.vector_db.search_topics(query, limit=limit)
            
            # If we don't have enough topics, try expanding the search
            if len(topics) < limit:
                # Try to expand query terms
                expanded_terms = self.expand_query_with_synonyms(query)
                for term in expanded_terms:
                    if term != query:
                        term_topics = self.vector_db.search_topics(term, limit=limit)
                        # Add unique topics
                        for topic in term_topics:
                            if topic not in topics:
                                topics.append(topic)
                                if len(topics) >= limit:
                                    break
                        if len(topics) >= limit:
                            break
            
            logger.info(f"Topic search for '{query}' returned {len(topics)} results")
            return topics[:limit]
        except Exception as e:
            logger.error(f"Error in topic search: {e}")
            return []  # Return empty list in case of error