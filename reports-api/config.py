from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Keycloak
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "reports-realm"
    keycloak_client_id: str = "reports-api"
    keycloak_client_secret: str = "oNwoLQdvJAvRcL89SydqCWCe5ry1jMgq"

    # ClickHouse
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    clickhouse_database: str = "bionicpro"

    # CORS
    cors_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
