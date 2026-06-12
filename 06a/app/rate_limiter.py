import time
from fastapi import HTTPException
from .config import settings

def check_rate_limit(user_id: str, redis_client):
    """
    Sliding window rate limiter using Redis
    """
    key = f"rate_limit:{user_id}"
    current_time = time.time()
    
    # Xoá các request cũ hơn 60 giây
    redis_client.zremrangebyscore(key, 0, current_time - 60)
    
    # Đếm số request trong 60 giây qua
    request_count = redis_client.zcard(key)
    
    if request_count >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again in 60 seconds."
        )
        
    # Thêm request hiện tại vào tập hợp với score = timestamp
    redis_client.zadd(key, {str(current_time): current_time})
    redis_client.expire(key, 60)
    return True
