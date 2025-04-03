from typing import List
import os
import logging
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalSentenceTransformerEmbeddings(Embeddings):
    """Use sentence-transformers for embeddings."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the embeddings model.
        
        Args:
            model_name: The name of the sentence-transformers model to use
        """
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Initialized sentence transformer model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize sentence transformer: {e}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents.
        
        Args:
            texts: The documents to embed
            
        Returns:
            List of embeddings, one for each document
        """
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating document embeddings: {e}")
            # Return a zero embedding as fallback
            return [[0.0] * 384] * len(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a query.
        
        Args:
            text: The query to embed
            
        Returns:
            Embedding for the query
        """
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            # Return a zero embedding as fallback
            return [0.0] * 384