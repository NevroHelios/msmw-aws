#!/bin/bash
# Create minimal CSV-only extraction worker (no pip dependencies needed)
# boto3 is already in the Lambda runtime, CSV parsing uses stdlib

set -e

echo "📦 Creating CSV-only extraction worker..."

PROJ_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKER_DIR="$PROJ_ROOT/backend/lambdas/extraction_worker"
OUT_DIR="$PROJ_ROOT/lambda_packages"

mkdir -p "$OUT_DIR"
rm -rf "$WORKER_DIR/package_csv"
mkdir -p "$WORKER_DIR/package_csv/extractors"

# Copy only the handler and CSV extractor (no pip install needed)
cp "$WORKER_DIR/handler.py" "$WORKER_DIR/package_csv/"
cp "$WORKER_DIR/extractors/csv_extractor.py" "$WORKER_DIR/package_csv/extractors/"
touch "$WORKER_DIR/package_csv/extractors/__init__.py"

rm -f "$OUT_DIR/extraction_worker_csv_only.zip"
cd "$WORKER_DIR/package_csv"
zip -q -r "$OUT_DIR/extraction_worker_csv_only.zip" .
cd "$PROJ_ROOT"

echo "📊 Package size:"
du -sh "$OUT_DIR/extraction_worker_csv_only.zip"

echo "✅ CSV-only package created!"
