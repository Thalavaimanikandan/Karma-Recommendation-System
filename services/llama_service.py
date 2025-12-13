import logging
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class LlamaService:
    """LLaMA/Ollama API service"""
    
    def __init__(self, api_url: str = 'http://localhost:11434', model: str = 'llama3.2'):
        self.api_url = api_url.rstrip('/')
        self.model = model
        logger.info(f"✅ LLaMA service initialized: {api_url} ({model})")
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 200
    ) -> Optional[str]:
        """Generate text using LLaMA"""
        try:
            url = f"{self.api_url}/api/generate"
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                return response.json().get('response', '').strip()
            else:
                logger.error(f"❌ LLaMA API error: {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"❌ LLaMA generation failed: {e}")
            return None
    
    def detect_category(
        self,
        text: str,
        categories: list
    ) -> Optional[str]:
        """Detect category from text"""
        prompt = f"""Analyze this text and choose the MOST relevant category.

Text: "{text[:500]}"

Categories: {', '.join(categories)}

Reply with ONLY the category name, nothing else."""

        result = self.generate(prompt, temperature=0.2, max_tokens=10)
        
        if result:
            result = result.lower().strip()
            # Validate
            if result in [c.lower() for c in categories]:
                return result
        
        return None
    
    def is_available(self) -> bool:
        """Check if LLaMA service is available"""
        try:
            response = requests.get(f"{self.api_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False