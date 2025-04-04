from typing import Dict, Any, List, Tuple
import os
import logging
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from .llm_client import OllamaLLM, OllamaChat

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArticleAnalyzer:
    """Uses GenAI to analyze news articles and generate summaries and topics."""
    
    def __init__(self, model_name: str = "llama3"):
        """Initialize the article analyzer with LLM.
        
        Args:
            model_name: Name of the Ollama model to use
        """
        # Initialize the Ollama LLM
        try:
            self.llm = OllamaLLM(model_name=model_name, temperature=0.1)
            logger.info(f"Initialized OllamaLLM with model {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize OllamaLLM: {e}")
            # Fallback to direct implementation if LangChain integration fails
            self.llm = OllamaChat(model_name=model_name, temperature=0.1)
            logger.info(f"Fallback to OllamaChat with model {model_name}")
        
        # Create prompt templates
        self.summary_prompt = PromptTemplate(
            input_variables=["title", "text"],
            template="""
            Article Title: {title}
            
            Article Content: {text}
            
            Task: Step-by-step, identify the main points of the following academic article, explaining their significance as you go. 
            Summarize the following text in one clear and concise paragraph, capturing the key ideas without missing critical points.
            Ensure the summary is easy to understand and avoids excessive detail.
            The summary should be 3-5 sentences long and highlight the most important information. 
            Do not include phrases like "Here is a summary of the article:"
            Output should contain ONLY the summary content.
            """
        )
        
        self.topics_prompt = PromptTemplate(
            input_variables=["title", "text"],
            template="""
            Article Title: {title}
            
            Article Content: {text}
            
            Task: Extract 3-7 main topics from this article as a simple list of keywords.
            Each topic should be 1-3 words and relevant for search indexing.
            Your response should ONLY contain the topics, one per line, with no numbering, explanations, or phrases like "The main topics are".
            """
        )
        
        # Create chains
        self.summary_chain = LLMChain(llm=self.llm, prompt=self.summary_prompt)
        self.topics_chain = LLMChain(llm=self.llm, prompt=self.topics_prompt)
        
    def analyze_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a news article to generate summary and identify topics.
        
        Args:
            article: Dictionary containing article data
            
        Returns:
            Original article with added summary and topics
        """
        # Check if article text is too long and truncate if necessary
        # Ollama has context limits, so we'll truncate to be safe
        text = article['text'][:2000] if len(article['text']) > 2000 else article['text']
        
        try:
            # Generate summary
            summary = self.summary_chain.run(
                title=article['title'],
                text=text
            )
            
            # Extract topics
            topics_text = self.topics_chain.run(
                title=article['title'],
                text=text
            )
            
            # Parse topics from the response text
            topics = [topic.strip() for topic in topics_text.split('\n') if topic.strip()]
            
            # Add analysis to article
            article['summary'] = summary.strip()
            article['topics'] = topics[:7]  # Ensure max 7 topics
            
            logger.info(f"Successfully analyzed article: {article['title']}")
        except Exception as e:
            logger.error(f"Error analyzing article {article.get('title', 'Unknown')}: {e}")
            # Provide fallback values
            article['summary'] = "Summary generation failed."
            article['topics'] = ["news"]
        
        return article
        
    def analyze_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple articles.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Articles with added summaries and topics
        """
        analyzed_articles = []
        for article in articles:
            analyzed_article = self.analyze_article(article)
            analyzed_articles.append(analyzed_article)
            
        return analyzed_articles