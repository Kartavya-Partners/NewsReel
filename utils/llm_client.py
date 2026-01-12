"""LLM Client for interacting with Ollama and Google Gemini."""

from typing import Dict, Any, Optional
import requests
import os
import time
from loguru import logger
import google.generativeai as genai

class LLMClient:
    """Client for interacting with LLMs (Ollama or Gemini)."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM client.
        
        Args:
            config: LLM configuration
        """
        self.provider = config.get('provider', 'ollama')
        self.model = config.get('model', 'llama3')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.timeout = config.get('timeout', 30)
        
        # Initialize Gemini if selected
        if self.provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.warning("GOOGLE_API_KEY not found. Fallback to Ollama?")
                # For now, let it crash or handle gracefully later.
            else:
                genai.configure(api_key=api_key)
                logger.info(f"Initialized Gemini Client with model: {self.model}")
        else:
            logger.info(f"Initialized Ollama Client with model: {self.model}")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_retries: int = 2) -> str:
        """
        Generate text using the configured LLM provider.
        """
        if self.provider == "gemini":
            return self._generate_gemini(prompt, system_prompt, max_retries)
        else:
            return self._generate_ollama(prompt, system_prompt, max_retries)

    def _generate_gemini(self, prompt: str, system_prompt: Optional[str], max_retries: int) -> str:
        """Generate text using Google Gemini with 429 Retry Logic."""
        
        current_attempt = 0
        final_error = None
        
        while current_attempt <= max_retries:
            try:
                # Re-init model each time (stateless)
                model = genai.GenerativeModel(
                    model_name=self.model,
                    generation_config=genai.GenerationConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_tokens,
                    )
                )
                
                logger.debug(f"Sending request to Gemini: {self.model} (Attempt {current_attempt+1})")
                
                # Base Rate Limit Protection (20s) - proactive wait
                time.sleep(20)
                
                final_prompt = prompt
                if system_prompt:
                    final_prompt = f"System Instruction: {system_prompt}\n\nUser Request: {prompt}"
                    
                response = model.generate_content(final_prompt)
                
                if response.text:
                    logger.debug(f"Received Gemini response ({len(response.text)} chars)")
                    return response.text
                else:
                     raise ValueError("Empty response from Gemini")
                     
            except Exception as e:
                error_str = str(e)
                final_error = e
                
                # Check for Quota Limit (429)
                if "429" in error_str or "quota" in error_str.lower():
                    # High wait time for FREE TIER recovery (some need 60s)
                    wait_time = 65 
                    logger.warning(f"Gemini Quota Exceeded (429). Sleeping {wait_time}s before retry {current_attempt+1}/{max_retries}...")
                    time.sleep(wait_time)
                    current_attempt += 1
                else:
                    logger.error(f"Gemini generation failed: {e}")
                    raise Exception(f"Gemini Error: {e}")

        raise Exception(f"Gemini Quota Exhausted after {max_retries} retries. Error: {final_error}")

    def _generate_ollama(self, prompt: str, system_prompt: Optional[str], max_retries: int) -> str:
        """Generate text using local Ollama."""
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                url = f"{self.base_url}/api/generate"
                
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "context": [], 
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                }
                
                if system_prompt:
                    payload["system"] = system_prompt
                
                if attempt > 0:
                    logger.warning(f"Retry attempt {attempt}/{max_retries}")
                
                response = requests.post(url, json=payload, timeout=getattr(self, 'timeout', 600))
                response.raise_for_status()
                
                result = response.json()
                return result.get('response', '')
                
            except Exception as e:
                last_error = e
                logger.error(f"Ollama Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    import time
                    time.sleep(2)
        
        raise Exception(f"Ollama generation failed: {last_error}")

    def is_available(self) -> bool:
        """Check if provider is available."""
        if self.provider == "gemini":
            return bool(os.getenv("GOOGLE_API_KEY"))
        else:
            try:
                requests.get(f"{self.base_url}/api/tags", timeout=2)
                return True
            except:
                return False
