from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic.env_settings import BaseSettings

_inst: dict[str, Config] = {}
project_dir: Path = Path(__file__).absolute().parent.parent.parent


class LogMode(Enum):
    json = 'json'
    simple = 'simple'


class LogLevel(Enum):
    critical = 'critical'
    error = 'error'
    warning = 'warning'
    info = 'info'
    debug = 'debug'
    notset = 'notset'


class FilterBackend(Enum):
    in_memory = 'in_memory'
    redis = 'redis'


class Config(BaseSettings):
    # app
    log_format: LogMode = LogMode.simple
    log_level: LogLevel = LogLevel.info
    filter_backend: FilterBackend = Field(default=FilterBackend.in_memory)

    # slack
    slack_token: str
    slack_socket_mode_token: str

    # redis
    redis_url: str | None


def get_config(env_file: Path = project_dir / '.env') -> Config:
    try:
        config = _inst['conf']
    except KeyError:
        config = Config(_env_file=env_file)  # type: ignore[call-arg]
        _inst['conf'] = config

    return config
