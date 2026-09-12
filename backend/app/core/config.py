from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    app_name: str = "LapZap"
    db_user: str
    db_pass: str
    db_host: str
    db_port: int
    db_name: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 30
    rate_limit_per_minute: int

    evolution_api_url: str
    evolution_api_key: str
    evolution_instance_name: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="mysql+asyncmy",
            username=self.db_user,
            password=self.db_pass,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


settings = Settings()  # pyright: ignore[reportCallIssue]
