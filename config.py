from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BOT_", env_file=".env", env_file_encoding="utf-8", extra='ignore')
    
    TOKEN: str


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env", env_file_encoding="utf-8", extra='ignore')
    
    HOST: str = "localhost"
    PORT: int = 5432
    NAME: str = "arcana_bot"
    USER: str = "postgres"
    PASSWORD: str = "password"
    
    @property
    def URL(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_", env_file=".env", env_file_encoding="utf-8", extra='ignore')
    
    HOST: str = "localhost"
    PORT: int = 6379
    
    @property
    def URL(self) -> str:
        return f"redis://{self.HOST}:{self.PORT}"


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPENAI_", env_file=".env", env_file_encoding="utf-8", extra='ignore')
    
    API_KEY: str = ""
    MODEL: str = "gpt-4o-mini"
    MAX_TOKENS: int = 500
    TEMPERATURE: float = 0.7


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", env_file_encoding="utf-8", extra='ignore')
    
    WEBAPP_URL: str = "https://e696722740d6733ce8592753b9c29d4c.serveo.net"
    DEFAULT_BALANCE: int = 10
    REFERRAL_BONUS: int = 10
    SECRET_KEY: str = "default-secret-key"


class LogSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOG_", env_file=".env", env_file_encoding="utf-8", extra='ignore')
    
    LEVEL: str = "INFO"


class Settings:
    def __init__(self):
        self.bot = BotSettings()
        self.database = DatabaseSettings()
        self.redis = RedisSettings()
        self.app = AppSettings()
        self.log = LogSettings()
        self.openai = OpenAISettings()


settings = Settings()


