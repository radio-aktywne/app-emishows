from pathlib import Path

from emishows.config.base import BaseConfig


class DatabaseConfig(BaseConfig):
    host: str = "localhost"
    port: int = 34000
    password: str = "password"


class EmitimesConfig(BaseConfig):
    host: str = "localhost"
    port: int = 36000
    user: str = "user"
    password: str = "password"
    calendar: str = "emitimes"


class Config(BaseConfig):
    host: str = "0.0.0.0"
    port: int = 35000
    certs_dir: Path = "/etc/certs"
    db: DatabaseConfig = DatabaseConfig()
    emitimes: EmitimesConfig = EmitimesConfig()