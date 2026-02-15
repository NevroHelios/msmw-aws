"""
Pydantic models for data validation across the application.
"""
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator


class StoreModel(BaseModel):
    """Store information"""
    store_id: str = Field(..., description="Unique store identifier")
    store_name: str = Field(..., description="Store display name")
    state: str
    district: str
    risk_appetite: Literal["low", "moderate", "high"] = "moderate"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "store_id": "STORE001",
                "store_name": "Sharma Kirana",
                "state": "Tamil Nadu",
                "district": "Chennai",
                "risk_appetite": "moderate"
            }
        }


class UploadModel(BaseModel):
    """Upload metadata"""
    store_id: str
    upload_id: str
    file_type: Literal[
        "invoice_image",
        "receipt_image", 
        "sales_csv",
        "inventory_csv",
        "bank_statement_pdf"
    ]
    s3_path: str
    status: Literal["UPLOADED", "PROCESSING", "EXTRACTED", "FAILED"] = "UPLOADED"
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "store_id": "STORE001",
                "upload_id": "INV_20260215_001",
                "file_type": "invoice_image",
                "s3_path": "raw/invoices_images/store001_2026_02_15.jpg",
                "status": "UPLOADED"
            }
        }


class InvoiceItem(BaseModel):
    """Single item in an invoice"""
    item_name: str
    quantity: float
    unit_price: float
    gst_rate: float = Field(..., ge=0, le=28)  # GST rate between 0-28%
    
    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price
    
    @property
    def gst_amount(self) -> float:
        return self.subtotal * (self.gst_rate / 100)
    
    @property
    def total(self) -> float:
        return self.subtotal + self.gst_amount


class InvoiceData(BaseModel):
    """Extracted invoice data"""
    supplier_name: str
    invoice_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    invoice_number: Optional[str] = None
    items: List[InvoiceItem]
    total_amount: float
    gst_amount: Optional[float] = None
    payment_terms: Optional[str] = None
    
    @validator('items')
    def validate_items(cls, v):
        if len(v) == 0:
            raise ValueError("Invoice must have at least one item")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "supplier_name": "ABC Traders",
                "invoice_date": "2026-02-15",
                "invoice_number": "INV-2024-001",
                "items": [
                    {
                        "item_name": "Rice 25kg",
                        "quantity": 20,
                        "unit_price": 950,
                        "gst_rate": 5
                    }
                ],
                "total_amount": 19950,
                "gst_amount": 950
            }
        }


class ReceiptData(BaseModel):
    """Extracted receipt data"""
    merchant_name: str
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    total_amount: float
    items: Optional[List[dict]] = None
    payment_method: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "merchant_name": "SuperMart",
                "date": "2026-02-15",
                "total_amount": 450.50,
                "payment_method": "UPI"
            }
        }


class SalesRecord(BaseModel):
    """Single sales record from CSV"""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    product_name: str
    quantity: float
    unit_price: float
    customer_name: Optional[str] = None
    payment_mode: Optional[str] = None
    
    @property
    def total_amount(self) -> float:
        return self.quantity * self.unit_price


class ExtractedDataModel(BaseModel):
    """Stored extracted data in DynamoDB"""
    store_id: str
    record_id: str  # Same as upload_id
    type: Literal["invoice", "receipt", "sales", "inventory", "bank_statement"]
    data: dict  # InvoiceData, ReceiptData, etc. serialized
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_method: Literal["llm", "csv_parse", "ocr"] = "llm"
    
    class Config:
        json_schema_extra = {
            "example": {
                "store_id": "STORE001",
                "record_id": "INV_20260215_001",
                "type": "invoice",
                "data": {
                    "supplier_name": "ABC Traders",
                    "invoice_date": "2026-02-15",
                    "total_amount": 19950
                },
                "extraction_method": "llm"
            }
        }
