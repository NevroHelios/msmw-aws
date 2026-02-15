#!/bin/bash
# Re-package extraction worker with Lambda Layers to reduce size

set -e

echo "📦 Re-packaging extraction_worker with Lambda Layers..."

cd backend/lambdas/extraction_worker

# Create layer directory
mkdir -p layer/python

# Install heavy dependencies to layer
echo "Installing dependencies to layer..."
pip install -q \
google-generativeai pandas pillow \
  -t layer/python/

# Package layer
echo "Creating layer package..."
cd layer
zip -q -r ../../../../lambda_packages/extraction_worker_layer.zip python/
cd ..

# Create minimal Lambda package (code only, lighter dependencies)
echo "Creating minimal Lambda package..."
rm -rf package
mkdir -p package

# Copy application code
cp -r extractors llm_clients handler.py package/

# Copy only shared code
cp -r ../../shared/*.py package/

# Install ONLY the light dependencies directly in package
pip install -q boto3 pydantic python-dotenv PyYAML openai python-docx PyPDF2 -t package/

# Package Lambda
cd package
zip -q -r ../../../../lambda_packages/extraction_worker_minimal.zip .
cd ../../../..

echo "📊 New package sizes:"
ls -lh lambda_packages/extraction_worker*

echo "✅ Re-packaging complete!"
