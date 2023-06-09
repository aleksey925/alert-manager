from __future__ import annotations

import os
import typing as t
from enum import Enum
from pathlib import Path

from pydantic import Field, Json, validator
from pydantic.env_settings import (
    BaseSettings,
    EnvSettingsSource,
    InitSettingsSource,
    SecretsSettingsSource,
)
from pydantic_vault import vault_config_settings_source

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


class LogTimestampFmt(Enum):
    unix = 'unix'
    unix_ms = 'unix_ms'
    iso = 'iso'


class FilterBackend(Enum):
    in_memory = 'in_memory'
    redis = 'redis'


VAULT_ADDR = os.environ.get('VAULT_ADDR')
VAULT_SECRET_PATH = os.environ.get('VAULT_SECRET_PATH')


class Config(BaseSettings):
    # app
    log_format: LogMode = LogMode.simple
    log_level: LogLevel = LogLevel.info
    log_timestamp_format: LogTimestampFmt = LogTimestampFmt.iso
    filter_backend: FilterBackend = Field(default=FilterBackend.in_memory)
    router_prefix: str = ''
    accounts_: Json[t.Any] | None = Field(
        env='ACCOUNTS', vault_secret_path=VAULT_SECRET_PATH, vault_secret_key='accounts'
    )

    # sentry
    sentry_dsn: str | None
    sentry_ca_certs: str | None

    # slack
    slack_token: str = Field(vault_secret_path=VAULT_SECRET_PATH, vault_secret_key='slack_token')
    slack_socket_mode_token: str = Field(
        vault_secret_path=VAULT_SECRET_PATH, vault_secret_key='slack_socket_mode_token'
    )

    # redis
    redis_url: str | None = Field(vault_secret_path=VAULT_SECRET_PATH, vault_secret_key='redis_url')

    @validator('router_prefix')
    def router_prefix_validator(cls, value: str, **kwargs: t.Any) -> str:  # noqa: N805
        if value:
            if not value.startswith('/'):
                raise ValueError('Must start with /')
            if value.endswith('/'):
                raise ValueError('Must not end with /')
        return value

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

        @classmethod
        def customise_sources(
            cls,
            init_settings: InitSettingsSource,
            env_settings: EnvSettingsSource,
            file_secret_settings: SecretsSettingsSource,
        ) -> tuple[t.Callable[[BaseSettings], dict[str, t.Any]], ...]:
            optional_sources = []
            if VAULT_ADDR:
                optional_sources.append(vault_config_settings_source)
            return init_settings, env_settings, *optional_sources


def get_config() -> Config:
    try:
        config = _inst['conf']
    except KeyError:
        config = Config()  # type: ignore[call-arg]
        _inst['conf'] = config

    return config
