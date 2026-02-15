#!/bin/bash
# Package Lambda functions for deployment

set -e

echo "📦 Packaging Lambda functions..."

# Create lambda_packages directory
mkdir -p lambda_packages

# Package Upload Handler
echo "Packaging upload_handler..."
cd backend/lambdas/upload_handler
zip -r ../../../lambda_packages/upload_handler.zip handler.py
if [ -f requirements.txt ]; then
    pip install -r requirements.txt -t package/
    cd package && zip -r ../../../../lambda_packages/upload_handler.zip . && cd ..
    rm -rf package
fi
cd ../../..

# Package Extraction Worker (more complex with dependencies)
echo "Packaging extraction_worker..."
cd backend/lambdas/extraction_worker
mkdir -p package

# Install Python dependencies
pip install -r requirements.txt -t package/

# Copy Lambda code
cp handler.py package/
cp -r extractors package/
cp -r llm_clients package/

# Create zip
cd package
zip -r ../../../../lambda_packages/extraction_worker.zip .
cd ..
rm -rf package
cd ../../..

# Check sizes
echo "📊 Package sizes:"
ls -lh lambda_packages/

echo "✅ Lambda packaging complete!"
