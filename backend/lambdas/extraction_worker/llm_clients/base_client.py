"""
Base LLM Client - Abstract interface for LLM providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self, api_key: str, temperature: float = 0.1):
        """
        Initialize LLM client.
        
        Args:
            api_key: API key for the LLM provider
            temperature: Sampling temperature (0.0-1.0)
        """
        self.api_key = api_key
        self.temperature = temperature
    
    @abstractmethod
    def extract_from_image(
        self, 
        image_data: bytes,
        prompt: str,
        mime_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Extract structured data from an image.
        
        Args:
            image_data: Image file bytes
            prompt: Extraction prompt
            mime_type: Image MIME type
        
        Returns:
            Extracted data as dictionary
        
        Raises:
            Exception if extraction fails
        """
        pass
    
    @abstractmethod
    def extract_from_text(
        self,
        text: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Extract structured data from text.
        
        Args:
            text: Input text
            prompt: Extraction prompt
        
        Returns:
            Extracted data as dictionary
        
        Raises:
            Exception if extraction fails
        """
        pass
    
    def validate_json_response(self, response: str) -> Dict[str, Any]:
        """
        Validate and parse JSON from LLM response.
        
        Args:
            response: LLM response string
        
        Returns:
            Parsed JSON dictionary
        
        Raises:
            ValueError if response is not valid JSON
        """
        import json
        import re
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)
        
        # Remove any leading/trailing text
        response = response.strip()
        
        # Find first '{' and last '}'
        start = response.find('{')
        end = response.rfind('}')
        
        if start != -1 and end != -1:
            response = response[start:end+1]
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {response}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
    
    def retry_with_backoff(self, func, max_retries: int = 3):
        """
        Retry function with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retries
        
        Returns:
            Function result
        
        Raises:
            Last exception if all retries fail
        """
        import time
        
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
