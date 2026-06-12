from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Production Agent"
    app_version: str = "1.0.0"
    environment: str = "production"
    port: int = 8000
    host: str = "0.0.0.0"
    
    # Security
    agent_api_key: str = "secret-key-123"
    
    # Redis for Rate Limit & Cost Guard
    redis_url: str = "redis://redis:6379/0"  # For docker-compose
    rate_limit_per_minute: int = 10
    monthly_budget_usd: float = 10.0

    class Config:
        env_file = ".env"

settings = Settings()
