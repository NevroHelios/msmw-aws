"""
Image Extractor - Extract data from invoice/receipt images using LLM
"""
import logging
from typing import Dict, Any
import os

logger = logging.getLogger(__name__)

# Extraction prompts for different image types
INVOICE_PROMPT = """
Extract structured invoice data from this image.

Return ONLY valid JSON with this exact structure (no other text):
{
  "supplier_name": "string - name of the supplier/vendor",
  "invoice_date": "YYYY-MM-DD format",
  "invoice_number": "string - invoice number if visible, otherwise null",
  "items": [
    {
      "item_name": "string - product/service name",
      "quantity": number,
      "unit_price": number,
      "gst_rate": number (0-28, GST percentage)
    }
  ],
  "total_amount": number - total invoice amount including GST,
  "gst_amount": number - total GST amount if visible, otherwise null,
  "payment_terms": "string - payment terms if visible, otherwise null"
}

If you cannot find a field, use null. All numbers should be numeric, not strings.
"""

RECEIPT_PROMPT = """
Extract structured receipt data from this image.

Return ONLY valid JSON with this exact structure (no other text):
{
  "merchant_name": "string - store/merchant name",
  "date": "YYYY-MM-DD format",
  "total_amount": number - total amount paid,
  "items": [
    {
      "name": "string - item name",
      "price": number
    }
  ],
  "payment_method": "string - payment method (UPI/Card/Cash) if visible, otherwise null"
}

If you cannot find a field, use null.
"""


class ImageExtractor:
    """Extract data from images using LLM"""
    
    def __init__(self, llm_client):
        """
        Initialize image extractor.
        
        Args:
            llm_client: LLM client instance (Gemini or OpenAI)
        """
        self.llm_client = llm_client
    
    def extract(self, image_data: bytes, file_type: str, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """
        Extract data from image.
        
        Args:
            image_data: Image file bytes
            file_type: Type of document (invoice_image, receipt_image, etc.)
            mime_type: Image MIME type
        
        Returns:
            Extracted data dictionary
        """
        # Get appropriate prompt
        prompt = self._get_prompt(file_type)
        
        logger.info(f"Extracting {file_type} using {self.llm_client.__class__.__name__}")
        
        # Call LLM
        extracted_data = self.llm_client.extract_from_image(
            image_data=image_data,
            prompt=prompt,
            mime_type=mime_type
        )
        
        logger.info(f"Successfully extracted {file_type}")
        return extracted_data
    
    def _get_prompt(self, file_type: str) -> str:
        """Get extraction prompt based on file type"""
        if file_type in ['invoice_image', 'purchase_order_image']:
            return INVOICE_PROMPT
        elif file_type == 'receipt_image':
            return RECEIPT_PROMPT
        else:
            # Generic prompt
            return """
            Extract all visible text and data from this image.
            Return as JSON with relevant fields.
            """
