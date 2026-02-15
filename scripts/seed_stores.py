#!/usr/bin/env python3
"""
Seed initial store data into DynamoDB
"""
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Stores')

# Sample stores
stores = [
    {
        'store_id': 'STORE001',
        'store_name': 'Sharma Kirana Store',
        'state': 'Tamil Nadu',
        'district': 'Chennai',
        'risk_appetite': 'moderate',
        'created_at': datetime.utcnow().isoformat()
    },
    {
        'store_id': 'STORE002',
        'store_name': 'Patel General Store',
        'state': 'Gujarat',
        'district': 'Ahmedabad',
        'risk_appetite': 'low',
        'created_at': datetime.utcnow().isoformat()
    },
    {
        'store_id': 'STORE003',
        'store_name': 'Kumar Retail Mart',
        'state': 'Karnataka',
        'district': 'Bangalore',
        'risk_appetite': 'high',
        'created_at': datetime.utcnow().isoformat()
    }
]

print("🌱 Seeding store data...")

for store in stores:
    try:
        table.put_item(Item=store)
        print(f"✅ Created: {store['store_id']} - {store['store_name']}")
    except Exception as e:
        print(f"❌ Error creating {store['store_id']}: {e}")

print("\n✅ Seeding complete!")
print(f"Created {len(stores)} stores in DynamoDB")
