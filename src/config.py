"""NexusOps configuration."""

import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Qwen / DashScope
    dashscope_api_key: str = Field(default="", alias="DASHSCOPE_API_KEY")
    dashscope_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    # Models
    model_reasoning: str = "qwen3-coder-next"
    model_fast: str = "qwen-plus"
    model_vision: str = "qwen3-vl-plus"
    model_embedding: str = "text-embedding-v3"

    # Database
    postgres_url: str = Field(
        default="postgresql+asyncpg://nexusops:password@localhost:5432/nexusops",
        alias="POSTGRES_URL"
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Email
    smtp_host: str = Field(default="smtpdm.aliyuncs.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=465, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_pass: str = Field(default="", alias="SMTP_PASS")

    # OSS
    oss_endpoint: str = Field(default="", alias="OSS_ENDPOINT")
    oss_bucket: str = Field(default="nexusops-documents", alias="OSS_BUCKET")

    # App
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    debug: bool = False
    human_approval_threshold: float = 0.7
    max_agent_iterations: int = 10
    memory_window_hours: int = 24
    memory_decay_days: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
