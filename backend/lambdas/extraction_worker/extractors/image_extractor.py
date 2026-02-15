"""
Image Extractor using Gemini REST API (pure HTTP, no SDK)
Extracts invoice/receipt data from images using Gemini Vision
"""
import json
import base64
import os
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

def extract_from_image(file_content: bytes, file_name: str) -> Dict[str, Any]:
    """
    Extract invoice/receipt data from image using Gemini Vision API
    Uses pure HTTP requests - no heavy SDK dependencies
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")
    
    # Determine if it's invoice or receipt
    doc_type = "invoice" if "invoice" in file_name.lower() else "receipt"
    
    # Encode image to base64
    image_b64 = base64.b64encode(file_content).decode('utf-8')
    
    # Determine MIME type
    mime_type = "image/jpeg"
    if file_name.lower().endswith('.png'):
        mime_type = "image/png"
    elif file_name.lower().endswith('.webp'):
        mime_type = "image/webp"
    
    # Gemini Vision API endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # Prompt for extraction
    prompt = f"""Extract all information from this {doc_type} image and return it as JSON.

For invoices, extract:
- invoice_number
- date (ISO format)
- vendor_name
- total_amount
- currency
- items (array of {{name, quantity, unit_price, total}})

For receipts, extract:
- receipt_number (if available)
- date (ISO format)
- store_name
- total_amount
- currency
- items (array of {{name, quantity, price}})

Return ONLY valid JSON, no markdown or explanations."""
    
    # Request payload
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": image_b64
                    }
                }
            ]
        }]
    }
    
    # Make HTTP request
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            # Extract text from response
            text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Clean up JSON (remove markdown if present)
            text = text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            # Parse extracted JSON
            extracted_data = json.loads(text)
            
            return {
                'type': doc_type,
                'data': extracted_data,
                'raw_response': text
            }
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"Gemini API error: {e.code} - {error_body}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse extracted data as JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"Image extraction failed: {str(e)}")
