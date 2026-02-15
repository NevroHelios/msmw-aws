"""
OpenAI LLM Client (PAID - fallback only)
"""
import os
import base64
import logging
from typing import Dict, Any
from openai import OpenAI
from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI API client for document extraction"""
    
    def __init__(
        self, 
        api_key: str = None,
        model_vision: str = "gpt-4o-mini",
        model_text: str = "gpt-4o-mini",
        temperature: float = 0.1
    ):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model_vision: Vision model (gpt-4o-mini or gpt-4-vision-preview)
            model_text: Text model
            temperature: Sampling temperature
        """
        super().__init__(api_key or os.getenv('OPENAI_API_KEY'), temperature)
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model_vision = model_vision
        self.model_text = model_text
        
        logger.info(f"Initialized OpenAI client with vision={model_vision}, text={model_text}")
    
    def extract_from_image(
        self, 
        image_data: bytes,
        prompt: str,
        mime_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Extract structured data from image using GPT-4 Vision.
        
        Args:
            image_data: Image file bytes
            prompt: Extraction prompt
            mime_type: Image MIME type
        
        Returns:
            Extracted data as dictionary
        """
        def _extract():
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create message with image
            response = self.client.chat.completions.create(
                model=self.model_vision,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data extraction assistant. Extract information from images and return ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=self.temperature,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content
            logger.debug(f"OpenAI image response: {response_text}")
            
            # Parse and validate JSON
            return self.validate_json_response(response_text)
        
        return self.retry_with_backoff(_extract)
    
    def extract_from_text(
        self,
        text: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Extract structured data from text using GPT.
        
        Args:
            text: Input text to extract from
            prompt: Extraction prompt with schema
        
        Returns:
            Extracted data as dictionary
        """
        def _extract():
            response = self.client.chat.completions.create(
                model=self.model_text,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data extraction assistant. Extract information from text and return ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nInput text:\n{text}"
                    }
                ],
                temperature=self.temperature,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content
            logger.debug(f"OpenAI text response: {response_text}")
            
            # Parse and validate JSON
            return self.validate_json_response(response_text)
        
        return self.retry_with_backoff(_extract)
    
    @staticmethod
    def is_available() -> bool:
        """Check if OpenAI API key is configured"""
        return bool(os.getenv('OPENAI_API_KEY'))
