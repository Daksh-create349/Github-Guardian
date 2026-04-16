from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    github_token: str = ""
    database_url: str = "sqlite:///./test.db"
    redis_url: str = "redis://localhost:6379/0"
    slack_webhook_url: str = ""
    webhook_secret: str = ""
    openrouter_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
