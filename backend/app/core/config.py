from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus


class Settings(BaseSettings):
    app_name: str = "Makan Society API"
    app_version: str = "0.1.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    jwt_secret_key: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    mssql_host: str = "mssql"
    mssql_port: int = 1433
    mssql_db: str = "SocietyApp"
    mssql_user: str = "sa"
    mssql_sa_password: str = "SocietyDev@2026!"
    redis_url: str = "redis://redis:6379/0"
    sms_provider_mode: str = "simulated"
    bulksmsbd_api_key: str | None = None
    bulksmsbd_sender_id: str | None = None
    bulksmsbd_base_url: str = "https://bulksmsbd.net/api/"
    bulksmsbd_timeout_seconds: int = 15
    bulksmsbd_enabled: bool = False
    bulksmsbd_dry_run: bool = True

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def sqlalchemy_url(self) -> str:
        params = "driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes&Encrypt=no"
        user = quote_plus(self.mssql_user)
        password = quote_plus(self.mssql_sa_password)
        return (
            f"mssql+pyodbc://{user}:{password}"
            f"@{self.mssql_host}:{self.mssql_port}/{self.mssql_db}?{params}"
        )


settings = Settings()
