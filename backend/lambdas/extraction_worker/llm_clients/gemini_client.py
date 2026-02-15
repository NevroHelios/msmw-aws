"""
Gemini LLM Client (FREE tier - recommended)
"""
import os
import base64
import logging
from typing import Dict, Any
import google.generativeai as genai
from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Gemini API client for document extraction"""
    
    def __init__(
        self, 
        api_key: str = None,
        model_vision: str = "gemini-1.5-flash",
        model_text: str = "gemini-1.5-flash",
        temperature: float = 0.1
    ):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (from Google AI Studio)
            model_vision: Vision model name
            model_text: Text model name
            temperature: Sampling temperature
        """
        super().__init__(api_key or os.getenv('GEMINI_API_KEY'), temperature)
        
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        genai.configure(api_key=self.api_key)
        
        self.model_vision = model_vision
        self.model_text = model_text
        
        logger.info(f"Initialized Gemini client with vision={model_vision}, text={model_text}")
    
    def extract_from_image(
        self, 
        image_data: bytes,
        prompt: str,
        mime_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Extract structured data from image using Gemini Vision.
        
        Args:
            image_data: Image file bytes
            prompt: Extraction prompt
            mime_type: Image MIME type
        
        Returns:
            Extracted data as dictionary
        """
        def _extract():
            model = genai.GenerativeModel(self.model_vision)
            
            # Prepare image parts
            image_parts = [
                {
                    "mime_type": mime_type,
                    "data": base64.b64encode(image_data).decode('utf-8')
                }
            ]
            
            # Full prompt
            full_prompt = f"{prompt}\n\nReturn ONLY valid JSON, no other text."
            
            # Generate response
            response = model.generate_content(
                [full_prompt, image_parts[0]],
                generation_config=genai.GenerationConfig(
                    temperature=self.temperature,
                )
            )
            
            # Extract text from response
            if not response.parts:
                raise ValueError("Empty response from Gemini")
            
            response_text = response.parts[0].text
            logger.debug(f"Gemini image response: {response_text}")
            
            # Parse and validate JSON
            return self.validate_json_response(response_text)
        
        return self.retry_with_backoff(_extract)
    
    def extract_from_text(
        self,
        text: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Extract structured data from text using Gemini.
        
        Args:
            text: Input text to extract from
            prompt: Extraction prompt with schema
        
        Returns:
            Extracted data as dictionary
        """
        def _extract():
            model = genai.GenerativeModel(self.model_text)
            
            # Combine prompt and text
            full_prompt = f"{prompt}\n\nInput text:\n{text}\n\nReturn ONLY valid JSON, no other text."
            
            # Generate response
            response = model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=self.temperature,
                )
            )
            
            # Extract text from response
            if not response.parts:
                raise ValueError("Empty response from Gemini")
            
            response_text = response.parts[0].text
            logger.debug(f"Gemini text response: {response_text}")
            
            # Parse and validate JSON
            return self.validate_json_response(response_text)
        
        return self.retry_with_backoff(_extract)
    
    @staticmethod
    def is_available() -> bool:
        """Check if Gemini API key is configured"""
        return bool(os.getenv('GEMINI_API_KEY'))
