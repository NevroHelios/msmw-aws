# Local Development Guide

Run the system locally without deploying to AWS (useful for development and testing).

## Option 1: LocalStack (AWS Emulator)

LocalStack emulates AWS services on your local machine (**FREE**).

### Setup

```bash
# Install LocalStack
pip install localstack localstack-client awscli-local

# Start LocalStack
localstack start -d

# Verify it's running
localstack status
```

### Configure for Local Development

Update `config/.env`:
```bash
USE_LOCALSTACK=true
LOCALSTACK_ENDPOINT=http://localhost:4566
```

### Create Local Resources

```bash
# Create S3 bucket
awslocal s3 mb s3://msme-retail-intelligence-local

# Create DynamoDB tables
awslocal dynamodb create-table \
  --table-name Stores \
  --attribute-definitions AttributeName=store_id,AttributeType=S \
  --key-schema AttributeName=store_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Repeat for Uploads and ExtractedData tables
```

### Run Lambda Functions Locally

```bash
# Install SAM CLI
pip install aws-sam-cli

# Test upload handler
cd backend/lambdas/upload_handler
sam local invoke -e test_event.json
```

---

## Option 2: Pure Local (No AWS)

Run completely locally using file system storage.

### Setup

```bash
# Create local storage directories
mkdir -p local_storage/raw/invoices_images
mkdir -p local_storage/raw/sales_csv
mkdir -p local_storage/processed

# Install dependencies
cd backend/lambdas/extraction_worker
pip install -r requirements.txt
```

### Run Extraction Locally

```python
# test_local.py
import os
os.environ['GEMINI_API_KEY'] = 'your-key-here'

from extractors.image_extractor import ImageExtractor
from llm_clients.gemini_client import GeminiClient

# Initialize
gemini = GeminiClient()
extractor = ImageExtractor(gemini)

# Test extraction
with open('test_invoice.jpg', 'rb') as f:
    image_data = f.read()

result = extractor.extract(
    image_data=image_data,
    file_type='invoice_image',
    mime_type='image/jpeg'
)

print(result)
```

---

## Option 3: Mock LLM Responses

For testing without using LLM API calls:

Update `config/.env`:
```bash
MOCK_LLM=true
```

Create `backend/lambdas/extraction_worker/llm_clients/mock_client.py`:

```python
from .base_client import BaseLLMClient

class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing"""
    
    def extract_from_image(self, image_data, prompt, mime_type="image/jpeg"):
        # Return fake invoice data
        return {
            "supplier_name": "Test Supplier",
            "invoice_date": "2026-02-15",
            "items": [
                {
                    "item_name": "Test Product",
                    "quantity": 10,
                    "unit_price": 100,
                    "gst_rate": 18
                }
            ],
            "total_amount": 1180
        }
    
    def extract_from_text(self, text, prompt):
        return {"mock": "data"}
```

---

## Testing Workflow

### 1. Test CSV Extraction (No LLM needed)

```bash
cd backend/lambdas/extraction_worker

python3 -c "
from extractors.csv_extractor import CSVExtractor
import sys

# Create test CSV
csv_data = b'''date,product,quantity,price
2026-02-15,Rice 25kg,10,950
2026-02-15,Wheat 10kg,20,400'''

extractor = CSVExtractor()
result = extractor.extract(csv_data, 'sales_csv')
print(result)
"
```

### 2. Test Image Extraction (Requires Gemini API)

```bash
# Set API key
export GEMINI_API_KEY="your-key-here"

python3 -c "
from extractors.image_extractor import ImageExtractor
from llm_clients.gemini_client import GeminiClient

gemini = GeminiClient()
extractor = ImageExtractor(gemini)

# Load test image
with open('test_invoice.jpg', 'rb') as f:
    image_data = f.read()

result = extractor.extract(image_data, 'invoice_image')
print(result)
"
```

### 3. Test Full Lambda Handler Locally

```bash
cd backend/lambdas/extraction_worker

# Create test event
cat > test_event.json << EOF
{
  "upload_id": "TEST_001",
  "store_id": "STORE001",
  "s3_path": "raw/invoices_images/test.jpg",
  "file_type": "invoice_image"
}
EOF

# Run handler (requires AWS credentials or LocalStack)
python3 -c "
import json
import handler

with open('test_event.json') as f:
    event = json.load(f)

result = handler.lambda_handler(event, None)
print(result)
"
```

---

## Recommended Development Flow

1. **Start with CSV extraction** (no LLM, fastest to test)
2. **Test Gemini API** with a single image locally
3. **Set up LocalStack** for full AWS emulation
4. **Deploy to AWS** once everything works locally

This saves on LLM API costs during development! 💡

---

## Local Testing Checklist

- [ ] CSV extractor works with test data
- [ ] Gemini client connects and extracts from test image
- [ ] Image extractor produces valid JSON
- [ ] Document extractor handles PDF/DOCX
- [ ] Mock LLM returns expected format (for unit tests)
- [ ] LocalStack setup complete (optional)
- [ ] All unit tests pass

Once all local tests pass, you're ready to deploy to AWS! 🚀
