import json
import math
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def calculate_safety_stock(d_avg, d_sigma, l_avg, l_sigma, z):
    """Greasley's Formula for Uncertainty"""
    # math: Z * sqrt( (L * sigma_d^2) + (D^2 * sigma_l^2) )
    term1 = l_avg * (d_sigma ** 2)
    term2 = (d_avg ** 2) * (l_sigma ** 2)
    return math.ceil(z * math.sqrt(term1 + term2))

def lambda_handler(event, context):
    # Event comes from the 'ExtractedData' DynamoDB or direct Step Function pass
    data = event.get('data', {})
    risk_appetite = event.get('store_profile', {}).get('risk_appetite', 'moderate')
    
    # Z-Scores for Risk Appetite
    z_map = {"low": 1.28, "moderate": 1.65, "high": 2.33}
    z = z_map.get(risk_appetite.lower(), 1.65)

    # Core Calculation
    avg_demand = data.get('avg_daily_demand', 10) # Fallback to 10 if missing
    
    safety_stock = calculate_safety_stock(
        avg_demand, 
        data.get('demand_std_dev', 2),
        data.get('supplier_lead_time_days', 3),
        data.get('lead_time_variance', 1),
        z
    )

    reorder_point = (avg_demand * data.get('supplier_lead_time_days', 3)) + safety_stock
    current_stock = data.get('current_stock', 0)

    result = {
        "item_id": data.get('item_id'),
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
        "status": "CRITICAL" if current_stock <= reorder_point else "HEALTHY",
        "recommendation": f"Order at least {reorder_point - current_stock} units" if current_stock <= reorder_point else "No action needed"
    }

    return {
        "statusCode": 200,
        "risk_report": result
    }