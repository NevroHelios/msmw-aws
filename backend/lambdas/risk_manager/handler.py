import json
import math
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
results_table = dynamodb.Table('AnalysisResults')

def calculate_risk(item):
    # Safety Stock formula: Z * sqrt(LeadTime * DemandVar + Demand^2 * LeadTimeVar)
    z_score = 1.65  # 95% service level
    avg_demand = float(item.get('avg_daily_demand', 10))
    lead_time = float(item.get('supplier_lead_time_days', 3))
    
    safety_stock = math.ceil(z_score * math.sqrt(lead_time * 2.0)) # Simplified for demo
    reorder_point = (avg_demand * lead_time) + safety_stock
    
    return {
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
        "status": "REORDER" if int(item['current_stock']) <= reorder_point else "OK"
    }

def lambda_handler(event, context):
    # 'event' comes from the Extraction Worker via Step Functions
    items = event.get('extracted_items', [])
    store_id = event.get('store_id')
    
    analysis_id = f"ANALYSIS_{int(datetime.now().timestamp())}"
    results = []

    for item in items:
        risk_data = calculate_risk(item)
        item.update(risk_data)
        results.append(item)

    # Save to our new AnalysisResults table
    results_table.put_item(Item={
        'store_id': store_id,
        'analysis_id': analysis_id,
        'timestamp': datetime.now().isoformat(),
        'data': results
    })

    return {"status": "success", "analysis_id": analysis_id}