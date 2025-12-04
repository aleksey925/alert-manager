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
from structlog import getLogger

logger = getLogger(__name__)
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
    log_health_check_is_enable: bool = True
    filter_backend: FilterBackend = Field(default=FilterBackend.in_memory)
    router_prefix: str = ''
    use_channel_id: bool = Field(default=False)
    accounts: Json[dict[str, str]] | None = Field(
        default=None,
        json_schema_extra={'vault_secret_path': VAULT_SECRET_PATH, 'vault_secret_key': 'accounts'},
    )

    # sentry
    sentry_dsn: str | None = Field(default=None)
    sentry_ca_certs: str | None = Field(default=None)

    # slack
    slack_token: str = Field(
        json_schema_extra={
            'vault_secret_path': VAULT_SECRET_PATH,
            'vault_secret_key': 'slack_token',
        }
    )
    slack_socket_mode_token: str = Field(
        json_schema_extra={
            'vault_secret_path': VAULT_SECRET_PATH,
            'vault_secret_key': 'slack_socket_mode_token',
        }
    )

    # redis
    redis_url: str | None = Field(
        default=None,
        json_schema_extra={'vault_secret_path': VAULT_SECRET_PATH, 'vault_secret_key': 'redis_url'},
    )
    redis_ssl_ca_certs_path: Path | None = None
    redis_ssl_ca_certs: str | None = Field(
        default=None,
        json_schema_extra={
            'vault_secret_path': VAULT_SECRET_PATH,
            'vault_secret_key': 'redis_ssl_ca_certs',
        },
    )
    redis_ssl_client_cert_path: Path | None = None
    redis_ssl_client_cert: str | None = Field(
        default=None,
        json_schema_extra={
            'vault_secret_path': VAULT_SECRET_PATH,
            'vault_secret_key': 'redis_ssl_client_cert',
        },
    )
    redis_ssl_client_key_path: Path | None = None
    redis_ssl_client_key: str | None = Field(
        default=None,
        json_schema_extra={
            'vault_secret_path': VAULT_SECRET_PATH,
            'vault_secret_key': 'redis_ssl_client_key',
        },
    )

    model_config: t.ClassVar[SettingsConfigDict] = SettingsConfigDict(env_file=project_dir / '.env', extra='ignore')

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
        else:
            logger.info('Vault integration is disabled. VAULT_ADDR env var is not set.')
        return init_settings, env_settings, dotenv_settings, *optional_sources


def save_secrets_to_file(config: Config) -> None:
    secrets = (
        (config.redis_ssl_ca_certs_path, config.redis_ssl_ca_certs, 'redis_ssl_ca_certs'),
        (config.redis_ssl_client_cert_path, config.redis_ssl_client_cert, 'redis_ssl_client_cert'),
        (config.redis_ssl_client_key_path, config.redis_ssl_client_key, 'redis_ssl_client_key'),
    )
    for path, content, secret_name in secrets:
        if not path and content:
            raise ValueError(f'Secret path {secret_name} is not set')
        if content is not None:
            path.write_text(content, encoding='utf-8')  # type: ignore[union-attr]


def get_config() -> Config:
    try:
        config = _inst['conf']
    except KeyError:
        config = Config()
        _inst['conf'] = config
        save_secrets_to_file(config)

    return config
