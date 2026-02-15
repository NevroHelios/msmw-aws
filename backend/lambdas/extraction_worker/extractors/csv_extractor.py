"""
CSV Extractor - Parse and structure CSV files
"""
import logging
from typing import Dict, Any, List
import pandas as pd
from io import StringIO, BytesIO

from decimal import Decimal

logger = logging.getLogger(__name__)


class CSVExtractor:
    """Extract data from CSV files"""
    
    def extract(self, file_data: bytes, file_type: str) -> Dict[str, Any]:
        """
        Extract data from CSV file.
        
        Args:
            file_data: CSV file bytes
            file_type: Type of CSV (sales_csv, inventory_csv, etc.)
        
        Returns:
            Structured data dictionary
        """
        logger.info(f"Extracting {file_type}")
        
        # Read CSV
        try:
            # Try UTF-8 first
            csv_string = file_data.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to latin-1
            csv_string = file_data.decode('latin-1')
        
        df = pd.read_csv(StringIO(csv_string))
        
        # Validate and transform based on file type
        if file_type == 'sales_csv':
            return self._extract_sales(df)
        elif file_type == 'inventory_csv':
            return self._extract_inventory(df)
        else:
            # Generic CSV extraction
            return {
                'rows': self._convert_floats_to_decimals(df.to_dict('records')),
                'row_count': len(df),
                'columns': df.columns.tolist()
            }
    
    def _extract_sales(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract sales data"""
        # Normalize column names (case-insensitive)
        df.columns = df.columns.str.lower().str.strip()
        
        # Required columns (flexible matching)
        required = ['date', 'product', 'quantity', 'price']
        column_mapping = {}
        
        for req in required:
            for col in df.columns:
                if req in col or col in req:
                    column_mapping[col] = req
                    break
        
        # Validate required columns exist
        if len(column_mapping) < len(required):
            raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")
        
        # Rename columns to standard names
        df = df.rename(columns=column_mapping)
        
        # Convert to records
        sales_records = []
        for _, row in df.iterrows():
            try:
                # Use Decimal for monetary/numeric values for DynamoDB
                qty = Decimal(str(row['quantity']))
                price = Decimal(str(row['price']))
                total = qty * price
                
                record = {
                    'date': str(row['date']),
                    'product_name': str(row['product']),
                    'quantity': qty,
                    'unit_price': price,
                    'total_amount': total
                }
                
                # Optional fields
                if 'customer' in df.columns:
                    record['customer_name'] = str(row['customer'])
                if 'payment' in df.columns or 'payment_mode' in df.columns:
                    payment_col = 'payment' if 'payment' in df.columns else 'payment_mode'
                    record['payment_mode'] = str(row[payment_col])
                
                sales_records.append(record)
            except Exception as e:
                logger.warning(f"Skipping invalid row: {e}")
                continue
        
        logger.info(f"Extracted {len(sales_records)} sales records")
        
        return {
            'records': sales_records,
            'total_records': len(sales_records),
            'total_amount': sum(r['total_amount'] for r in sales_records)
        }
    
    def _extract_inventory(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract inventory data"""
        df.columns = df.columns.str.lower().str.strip()
        
        # Convert to records using helper to handle floats
        inventory_records = self._convert_floats_to_decimals(df.to_dict('records'))
        
        logger.info(f"Extracted {len(inventory_records)} inventory records")
        
        return {
            'records': inventory_records,
            'total_records': len(inventory_records)
        }

    def _convert_floats_to_decimals(self, obj):
        """Recursively convert floats to Decimals for DynamoDB"""
        if isinstance(obj, list):
            return [self._convert_floats_to_decimals(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, float):
            return Decimal(str(obj))
        else:
            return obj
