from typing import Dict, Any, List, Tuple
import os
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


class ArticleAnalyzer:
    """Uses GenAI to analyze news articles and generate summaries and topics."""
    
    def __init__(self):
        """Initialize the article analyzer with LLM."""
        # Initialize the LLM
        api_key = os.getenv("OPENAI_API_KEY")
        self.llm = OpenAI(openai_api_key=api_key, temperature=0.1)
        
        # Create prompt templates
        self.summary_prompt = PromptTemplate(
            input_variables=["title", "text"],
            template="""
            Article Title: {title}
            
            Article Content: {text}
            
            Task: Generate a concise summary of the above news article that captures all key points.
            The summary should be 3-5 sentences long and highlight the most important information.
            
            Summary:
            """
        )
        
        self.topics_prompt = PromptTemplate(
            input_variables=["title", "text"],
            template="""
            Article Title: {title}
            
            Article Content: {text}
            
            Task: Extract the main topics from this news article. 
            Provide a list of 3-7 topics that accurately represent what the article is about.
            Each topic should be 1-3 words and should be relevant for search indexing.
            
            Topics:
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
        # Generate summary
        summary = self.summary_chain.run(
            title=article['title'],
            text=article['text'][:4000]  # Limit text length for API
        )
        
        # Extract topics
        topics_text = self.topics_chain.run(
            title=article['title'],
            text=article['text'][:4000]  # Limit text length for API
        )
        
        # Parse topics into a list
        topics = [topic.strip() for topic in topics_text.split('\n') if topic.strip()]
        
        # Add analysis to article
        article['summary'] = summary.strip()
        article['topics'] = topics
        
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
