"""LLM Client for interacting with Ollama."""

from typing import Dict, Any, Optional
import requests
from loguru import logger


class LLMClient:
    """Client for interacting with local LLM via Ollama."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM client.
        
        Args:
            config: LLM configuration
        """
        self.model = config.get('model', 'llama3')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.timeout = config.get('timeout', 300)  # Default 5 minutes
        
        logger.info(f"Initialized LLM client with model: {self.model} (timeout: {self.timeout}s)")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_retries: int = 2) -> str:
        """
        Generate text using the LLM with retry logic.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_retries: Number of retries on failure
            
        Returns:
            Generated text
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                url = f"{self.base_url}/api/generate"
                
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                }
                
                if system_prompt:
                    payload["system"] = system_prompt
                
                if attempt > 0:
                    logger.warning(f"Retry attempt {attempt}/{max_retries}")
                
                logger.debug(f"Sending request to Ollama: {self.model}")
                
                response = requests.post(url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                
                result = response.json()
                generated_text = result.get('response', '')
                
                logger.debug(f"Received response ({len(generated_text)} chars)")
                
                return generated_text
                
            except requests.exceptions.Timeout as e:
                last_error = e
                logger.error(f"Timeout on attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    logger.info("Retrying with reduced token count...")
                    # Reduce tokens for retry
                    self.max_tokens = max(200, self.max_tokens // 2)
                    
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.error(f"Error calling Ollama API: {e}")
                if attempt < max_retries:
                    import time
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        # All retries failed
        raise Exception(f"LLM generation failed after {max_retries + 1} attempts: {last_error}")
    
    def is_available(self) -> bool:
        """
        Check if Ollama is available.
        
        Returns:
            True if Ollama is running
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
