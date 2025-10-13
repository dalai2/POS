from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    env: str = "dev"
    secret_key: str = "change_me_super_secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 30
    database_url: str = "sqlite:///./dev.db"
    tenant_header: str = "X-Tenant-ID"
    backend_cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()



