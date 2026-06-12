from datetime import datetime
from fastapi import HTTPException
from .config import settings

def check_budget(user_id: str, estimated_cost: float, redis_client):
    """
    Cost guard: Chặn request nếu user vượt ngân sách trong tháng
    """
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    
    current_spent = float(redis_client.get(key) or 0)
    
    if current_spent + estimated_cost > settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail=f"Payment Required: Vượt quá ngân sách ${settings.monthly_budget_usd}/tháng."
        )
        
    # Cập nhật số tiền đã tiêu và set thời gian expire sang tháng sau
    redis_client.incrbyfloat(key, estimated_cost)
    redis_client.expire(key, 32 * 24 * 3600)  # Giữ data ~1 tháng
    return True
