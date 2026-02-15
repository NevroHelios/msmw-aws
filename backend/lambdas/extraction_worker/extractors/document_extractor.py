"""
Document Extractor - Extract text from PDF/DOCX and use LLM
"""
import logging
from typing import Dict, Any
import PyPDF2
from docx import Document
from io import BytesIO

logger = logging.getLogger(__name__)


class DocumentExtractor:
    """Extract data from documents (PDF, DOCX)"""
    
    def __init__(self, llm_client):
        """
        Initialize document extractor.
        
        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client
    
    def extract(self, file_data: bytes, file_type: str, file_name: str) -> Dict[str, Any]:
        """
        Extract data from document.
        
        Args:
            file_data: Document file bytes
            file_type: Type of document
            file_name: Original filename
        
        Returns:
            Extracted data dictionary
        """
        # Extract text based on file extension
        if file_name.lower().endswith('.pdf'):
            text = self._extract_pdf_text(file_data)
        elif file_name.lower().endswith('.docx'):
            text = self._extract_docx_text(file_data)
        else:
            # Try as plain text
            text = file_data.decode('utf-8', errors='ignore')
        
        logger.info(f"Extracted {len(text)} characters from document")
        
        # Use LLM to structure the text
        prompt = self._get_extraction_prompt(file_type)
        
        extracted_data = self.llm_client.extract_from_text(
            text=text,
            prompt=prompt
        )
        
        return extracted_data
    
    def _extract_pdf_text(self, file_data: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_file = BytesIO(file_data)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def _extract_docx_text(self, file_data: bytes) -> str:
        """Extract text from DOCX"""
        try:
            docx_file = BytesIO(file_data)
            doc = Document(docx_file)
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            return ""
    
    def _get_extraction_prompt(self, file_type: str) -> str:
        """Get extraction prompt based on file type"""
        if 'bank_statement' in file_type:
            return """
            Extract bank statement data from this text.
            
            Return ONLY valid JSON:
            {
              "account_number": "string",
              "statement_period": "string",
              "opening_balance": number,
              "closing_balance": number,
              "transactions": [
                {
                  "date": "YYYY-MM-DD",
                  "description": "string",
                  "debit": number or null,
                  "credit": number or null,
                  "balance": number
                }
              ]
            }
            """
        else:
            return """
            Extract all structured information from this document.
            Return as JSON with appropriate fields based on the content.
            """
