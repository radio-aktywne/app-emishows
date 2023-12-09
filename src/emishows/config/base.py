from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """Base configuration class."""

    model_config = SettingsConfigDict(
        env_prefix="EMISHOWS__",
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )
