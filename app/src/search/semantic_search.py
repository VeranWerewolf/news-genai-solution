from typing import Dict, Any, List
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
            
            Task: Enhance this search query for finding news articles. 
            Identify the key concepts, add relevant synonyms or related terms,
            and rewrite it to maximize semantic search effectiveness.
            
            Enhanced query:
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
            return enhanced_query.strip()
        except Exception as e:
            logger.error(f"Error enhancing query: {e}")
            return query  # Return original query if enhancement fails
        
    def search(self, query: str, enhance: bool = True, limit: int = 5, filter_by_topics: List[str] = None) -> List[Dict[str, Any]]:
        """
        Perform semantic search for news articles matching the query.
        
        Args:
            query: Search query
            enhance: Whether to enhance the query using AI
            limit: Maximum number of results to return
            filter_by_topics: Optional list of topics to filter results
            
        Returns:
            List of matching articles
        """
        try:
            # Enhance query if requested
            if enhance:
                search_query = self.enhance_query(query)
                logger.info(f"Enhanced query: '{query}' -> '{search_query}'")
            else:
                search_query = query
                
            # Search the vector database
            results = self.vector_db.search(search_query, limit=limit, filter_by_topics=filter_by_topics)
            
            # Log search results
            logger.info(f"Search for '{search_query}' returned {len(results)} results")
            
            return results
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []  # Return empty list in case of error
            
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
            # Get topics from vector DB
            topics = self.vector_db.search_topics(query, limit=limit)
            logger.info(f"Topic search for '{query}' returned {len(topics)} results")
            return topics
        except Exception as e:
            logger.error(f"Error in topic search: {e}")
            return []  # Return empty list in case of error
    
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
            Generate 5-8 synonyms or closely related terms for the search term: "{query}"
            
            Return only the list of terms, one per line, without numbering or explanation.
            """
            
            # Generate synonyms
            synonyms_text = self.llm(prompt)
            
            # Process the response
            synonyms = [term.strip() for term in synonyms_text.split('\n') if term.strip()]
            
            # Add original query as first term
            all_terms = [query] + synonyms
            
            # Remove duplicates and empty strings
            unique_terms = list(dict.fromkeys([term for term in all_terms if term]))
            
            logger.info(f"Expanded query '{query}' to {len(unique_terms)} terms")
            return unique_terms
            
        except Exception as e:
            logger.error(f"Error expanding query with synonyms: {e}")
            return [query]  # Return original query if expansion fails