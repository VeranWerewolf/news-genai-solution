import os
import json
import requests
from typing import Dict, Any, List, Optional
import logging

from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaLLM(LLM):
    """LLM wrapper for Ollama API."""
    
    api_url: str = os.getenv("LLM_API_URL", "http://ollama:11434/api")
    model_name: str = "llama3"  # Default model
    temperature: float = 0.1
    num_predict: int = 1024  # Equivalent to max_tokens
    top_p: float = 0.9
    
    @property
    def _llm_type(self) -> str:
        return "ollama"
    
    def _call(
        self, 
        prompt: str, 
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        """Call the Ollama API."""
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.num_predict,
                "top_p": self.top_p
            },
            "stream": False
        }
        
        if stop:
            data["options"]["stop"] = stop
        
        try:
            endpoint = f"{self.api_url}/generate"
            response = requests.post(endpoint, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Error calling Ollama API: {e}")
            # Provide a fallback response in case of errors
            return "I was unable to generate a response due to an error."
        
    def get_chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """Get completion from chat messages format."""
        headers = {
            "Content-Type": "application/json"
        }
        
        # Format messages for Ollama chat endpoint
        data = {
            "model": self.model_name,
            "messages": messages,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.num_predict,
                "top_p": self.top_p
            },
            "stream": False
        }
        
        try:
            endpoint = f"{self.api_url}/chat"
            response = requests.post(endpoint, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Error calling Ollama chat API: {e}")
            # Provide a fallback response in case of errors
            return "I was unable to generate a response due to an error."


class OllamaChat:
    """Chat model wrapper for Ollama API with simpler interface."""
    
    def __init__(
        self,
        model_name: str = "llama3",
        temperature: float = 0.1,
        num_predict: int = 1024,
        top_p: float = 0.9
    ):
        self.api_url = os.getenv("LLM_API_URL", "http://ollama:11434/api")
        self.model_name = model_name
        self.temperature = temperature
        self.num_predict = num_predict
        self.top_p = top_p
    
    def __call__(self, prompt: str) -> str:
        """Generate a response to the prompt."""
        return self._generate_completion(prompt)
    
    def _generate_completion(self, prompt: str) -> str:
        """Generate a text completion via Ollama API."""
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.num_predict,
                "top_p": self.top_p
            },
            "stream": False
        }
        
        try:
            endpoint = f"{self.api_url}/generate"
            response = requests.post(endpoint, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Error calling Ollama API: {e}")
            # Provide a fallback response in case of errors
            return "I was unable to generate a response due to an error."
            
    def run(self, prompt: str) -> str:
        """Run the model on the prompt (for compatibility with LangChain chains)."""
        return self._generate_completion(prompt)