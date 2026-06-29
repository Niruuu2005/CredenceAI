from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core
    APP_ENV: str = Field(default="local")
    APP_NAME: str = Field(default="credenceai")
    MOCK_SERVICES: bool = Field(default=False)
    CELERY_ALWAYS_EAGER: bool = Field(default=True)
    OPENAI_API_KEY: str | None = Field(default=None)
    DATABASE_URL: str = Field(default="postgresql://user:pass@localhost:5432/credenceai")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092")
    MINIO_ENDPOINT: str = Field(default="http://localhost:9000")
    MINIO_ACCESS_KEY: str = Field(default="change-me")
    MINIO_SECRET_KEY: str = Field(default="change-me")
    OPENSEARCH_URL: str = Field(default="http://localhost:9200")
    LOG_LEVEL: str = Field(default="INFO")

    # Source Adapter Configs
    SEARXNG_BASE_URL: str = Field(default="http://localhost:8080")
    ENABLE_WIKIDATA: bool = Field(default=True)
    ENABLE_WIKIPEDIA: bool = Field(default=True)
    ENABLE_GDELT: bool = Field(default=True)
    ENABLE_COMMONCRAWL: bool = Field(default=True)
    ENABLE_OPENALEX: bool = Field(default=True)
    ENABLE_CROSSREF: bool = Field(default=False)
    ENABLE_ARXIV: bool = Field(default=False)
    ENABLE_PAID_SERP: bool = Field(default=False)

    # Budgets & Defaults
    DEFAULT_MAX_SOURCES: int = Field(default=4)
    DEFAULT_MAX_URLS_TO_CRAWL: int = Field(default=20)
    DEFAULT_DEADLINE_MS: int = Field(default=12000)

    # Crawl Safety & Policy Configuration
    DEFAULT_CRAWL_RATE_LIMIT_DELAY: float = Field(default=1.0)
    CRAWL_MAX_FILE_SIZE: int = Field(default=5242880)  # 5MB
    CRAWL_BANNED_CIDRS: list[str] = Field(default_factory=lambda: [
        "127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
        "169.254.0.0/16", "224.0.0.0/4", "240.0.0.0/4", "::1/128",
        "fc00::/7", "fe80::/10", "::/128"
    ])

    # SDK / API Key Auth
    ENABLE_API_KEY_AUTH: bool = Field(default=False)
    API_KEY_HEADER_NAME: str = Field(default="X-API-Key")

    # CORS (split frontend deploy — set to your SPA origin in production)
    CORS_ALLOWED_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # Local-only developer login (disabled when unset)
    DEV_LOGIN_USERNAME: str | None = Field(default=None)
    DEV_LOGIN_PASSWORD: str | None = Field(default=None)

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=False)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)

    # SDK Metadata
    API_VERSION: str = Field(default="0.1.0")

    # Google OAuth & User Auth Settings
    GOOGLE_CLIENT_ID: str | None = Field(default=None)
    GOOGLE_CLIENT_SECRET: str | None = Field(default=None)
    GOOGLE_REDIRECT_URI: str | None = Field(default=None)
    JWT_SECRET: str = Field(default="change-me-in-production-1234567890")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRY_MINUTES: int = Field(default=1440)

    # Database pool (PostgreSQL)
    DB_POOL_SIZE: int = Field(default=5)
    DB_MAX_OVERFLOW: int = Field(default=10)
    DB_POOL_RECYCLE: int = Field(default=1800)

    # Stripe billing
    STRIPE_SECRET_KEY: str | None = Field(default=None)
    STRIPE_WEBHOOK_SECRET: str | None = Field(default=None)
    STRIPE_PRICE_ID_PRO: str | None = Field(default=None)
    STRIPE_PRICE_ID_ENTERPRISE: str | None = Field(default=None)
    STRIPE_SUCCESS_URL: str | None = Field(default=None)
    STRIPE_CANCEL_URL: str | None = Field(default=None)

settings = Settings()

