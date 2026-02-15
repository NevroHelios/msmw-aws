"""
CSV Extractor - Parse and structure CSV files
Uses only Python stdlib (no pandas dependency)
"""
import csv
import logging
from typing import Dict, Any, List
from io import StringIO
from decimal import Decimal

logger = logging.getLogger(__name__)


def extract_from_csv(file_data: bytes, file_type: str) -> Dict[str, Any]:
    """
    Extract data from CSV file.

    Args:
        file_data: CSV file bytes
        file_type: Type of CSV (sales_csv, inventory_csv, etc.)

    Returns:
        Structured data dictionary
    """
    logger.info(f"Extracting {file_type}")

    # Decode CSV bytes
    try:
        csv_string = file_data.decode('utf-8')
    except UnicodeDecodeError:
        csv_string = file_data.decode('latin-1')

    reader = csv.DictReader(StringIO(csv_string))
    rows = list(reader)

    if file_type == 'sales_csv':
        return _extract_sales(rows, reader.fieldnames or [])
    elif file_type == 'inventory_csv':
        return _extract_inventory(rows)
    else:
        # Generic CSV extraction
        return {
            'rows': _convert_numeric_to_decimals(rows),
            'row_count': len(rows),
            'columns': reader.fieldnames or []
        }


def _extract_sales(rows: List[Dict[str, str]], columns: List[str]) -> Dict[str, Any]:
    """Extract sales data"""
    # Normalize column names
    col_lower = [c.lower().strip() for c in columns]

    # Build flexible column mapping
    required = ['date', 'product', 'quantity', 'price']
    column_mapping = {}  # original_col -> standard_name

    for req in required:
        for orig, low in zip(columns, col_lower):
            if req in low or low in req:
                column_mapping[orig] = req
                break

    if len(column_mapping) < len(required):
        raise ValueError(f"Missing required columns. Found: {columns}")

    # Reverse map: standard_name -> original_col
    std_to_orig = {v: k for k, v in column_mapping.items()}

    # Find optional columns
    payment_col = None
    customer_col = None
    for orig, low in zip(columns, col_lower):
        if 'customer' in low:
            customer_col = orig
        if 'payment' in low:
            payment_col = orig

    sales_records = []
    for row in rows:
        try:
            qty = Decimal(str(row[std_to_orig['quantity']]).strip())
            price = Decimal(str(row[std_to_orig['price']]).strip())
            total = qty * price

            record = {
                'date': str(row[std_to_orig['date']]).strip(),
                'product_name': str(row[std_to_orig['product']]).strip(),
                'quantity': qty,
                'unit_price': price,
                'total_amount': total
            }

            if customer_col and row.get(customer_col):
                record['customer_name'] = str(row[customer_col]).strip()
            if payment_col and row.get(payment_col):
                record['payment_mode'] = str(row[payment_col]).strip()

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


def _extract_inventory(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    """Extract inventory data"""
    inventory_records = _convert_numeric_to_decimals(rows)

    logger.info(f"Extracted {len(inventory_records)} inventory records")

    return {
        'records': inventory_records,
        'total_records': len(inventory_records)
    }


def _convert_numeric_to_decimals(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Convert numeric string values to Decimals for DynamoDB"""
    result = []
    for row in rows:
        converted = {}
        for k, v in row.items():
            k = k.lower().strip()
            try:
                converted[k] = Decimal(v.strip())
            except Exception:
                converted[k] = v.strip() if isinstance(v, str) else v
        result.append(converted)
    return result
