from __future__ import annotations

import os
import typing as t
from enum import Enum
from pathlib import Path

from pydantic import Field, Json, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from pydantic_vault import VaultSettingsSource

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
    accounts: Json[dict[str, str]] | None = Field(
        default=None, vault_secret_path=VAULT_SECRET_PATH, vault_secret_key='accounts'
    )

    # sentry
    sentry_dsn: str | None = Field(default=None)
    sentry_ca_certs: str | None = Field(default=None)

    # slack
    slack_token: str = Field(vault_secret_path=VAULT_SECRET_PATH, vault_secret_key='slack_token')
    slack_socket_mode_token: str = Field(
        vault_secret_path=VAULT_SECRET_PATH, vault_secret_key='slack_socket_mode_token'
    )

    # redis
    redis_url: str | None = Field(
        default=None, vault_secret_path=VAULT_SECRET_PATH, vault_secret_key='redis_url'
    )

    model_config: t.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=project_dir / '.env', extra='ignore'
    )

    @field_validator('router_prefix')
    @classmethod
    def router_prefix_validator(cls, value: str, **kwargs: t.Any) -> str:
        if value:
            if not value.startswith('/'):
                raise ValueError('Must start with /')
            if value.endswith('/'):
                raise ValueError('Must not end with /')
        return value

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        optional_sources = []
        if VAULT_ADDR:
            optional_sources.append(VaultSettingsSource(settings_cls))
        return init_settings, env_settings, dotenv_settings, *optional_sources


def get_config() -> Config:
    try:
        config = _inst['conf']
    except KeyError:
        config = Config()  # type: ignore[call-arg]
        _inst['conf'] = config

    return config
