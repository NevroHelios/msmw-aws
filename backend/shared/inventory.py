from pydantic import BaseModel, Field
from typing import Optional

class InventoryItemSchema(BaseModel):
    item_id: str
    current_stock: int = Field(gt=-1)
    supplier_lead_time_days: float = Field(gt=0)
    lead_time_variance: float = Field(default=1.0)  # Standard deviation of delivery
    demand_std_dev: float = Field(default=5.0)      # Standard deviation of sales
    avg_daily_demand: Optional[float] = None