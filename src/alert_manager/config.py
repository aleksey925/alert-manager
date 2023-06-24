from __future__ import annotations

import typing as t
from enum import Enum
from pathlib import Path

from pydantic import Field, Json, validator
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
    accounts_: Json[t.Any] | None = Field(env='ACCOUNTS')

    # sentry
    sentry_dsn: str | None
    sentry_ca_certs: str | None

    # slack
    slack_token: str
    slack_socket_mode_token: str

    # redis
    redis_url: str | None

    @validator('accounts_')
    def accounts_validator(
        cls, value: t.Any, **kwargs: t.Any  # noqa: N805
    ) -> dict[str, str] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError('Must be a dict')
        if not all(
            all((isinstance(key, str), isinstance(value, str))) for key, value in value.items()
        ):
            raise ValueError('Key and value in dict must be string')
        return value

    @property
    def accounts(self) -> dict[str, str] | None:
        return self.accounts_

    class Config:
        env_file = project_dir / '.env'


def get_config() -> Config:
    try:
        config = _inst['conf']
    except KeyError:
        config = Config()  # type: ignore[call-arg]
        _inst['conf'] = config

    return config
