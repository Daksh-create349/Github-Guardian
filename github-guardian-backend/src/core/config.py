from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # GitHub API (server-level fallback)
    github_token: str = ""
    database_url: str = "sqlite:///./test.db"
    redis_url: str = "redis://localhost:6379/0"
    slack_webhook_url: str = ""
    webhook_secret: str = ""
    openrouter_api_key: str = ""
    openai_api_key: str = ""

    # GitHub OAuth App credentials
    github_client_id: str = ""
    github_client_secret: str = ""

    # JWT
    jwt_secret: str = "github_guardian_super_secret_jwt_key_2026"

    # URLs
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
