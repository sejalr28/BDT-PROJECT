from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres (app data: users, alerts) - host-side port from docker-compose
    database_url: str = "postgresql://appuser:apppass@localhost:5433/logplatform"

    # Elasticsearch (log search + stats aggregations)
    elasticsearch_url: str = "http://localhost:9200"
    logs_index: str = "hdfs-logs-parsed"

    # JWT
    jwt_secret: str = "dev-secret-change-me"  # override via JWT_SECRET env var
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 8  # 8 hours

    class Config:
        env_file = ".env"


settings = Settings()