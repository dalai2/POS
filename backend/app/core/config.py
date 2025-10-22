from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    env: str = "dev"
    secret_key: str = "change_me_super_secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 30
    database_url: str = "postgresql+psycopg2://erpuser:erppass@db:5432/erppos"
    tenant_header: str = "X-Tenant-ID"
    backend_cors_origins: str = "http://localhost:5173"
    
    # Railway specific - use PORT env var if available
    port: int = int(os.getenv("PORT", "8000"))
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string or ALLOWED_ORIGINS env var"""
        origins = self.backend_cors_origins
        return [origin.strip() for origin in origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()



