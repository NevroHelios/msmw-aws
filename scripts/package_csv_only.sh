#!/bin/bash
# Create minimal CSV-only extraction worker (no heavy dependencies)

set -e

echo "📦 Creating CSV-only extraction worker..."

cd backend/lambdas/extraction_worker

mkdir -p package_csv

# Copy only CSV extractor and shared code
cp handler.py package_csv/
mkdir -p package_csv/extractors
cp extractors/__init__.py extractors/csv_extractor.py package_csv/extractors/ 2>/dev/null || true

# Copy shared code
cp -r ../../shared/*.py package_csv/

# Install ONLY lightweight dependencies (no pandas, PIL, gemini!)
# CSV parsing can be done with standard library
pip install -q boto3 pydantic python-dotenv PyYAML -t package_csv/

cd package_csv
zip -q -r ../../../../lambda_packages/extraction_worker_csv_only.zip .
cd ../../../..

echo "📊 Package size:"
ls -lh lambda_packages/extraction_worker_csv_only.zip

echo "✅ CSV-only package created!"
