from fastapi import Header, HTTPException
from .config import settings

def verify_api_key(x_api_key: str = Header(..., description="API Key để xác thực")):
    if x_api_key != settings.agent_api_key:
        raise HTTPException(
            status_code=401, 
            detail="Unauthorized: Sai API Key mất rồi anh ơi!"
        )
    return "authorized_user"
