import typing as t
from functools import partial

import sentry_sdk
from aiohttp import web
from aiohttp_deps import Router, setup_swagger
from aiohttp_deps import init as deps_init
from redis.asyncio.client import Redis
from redis.connection import parse_url as parse_redis_url
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from slack_sdk.web.async_client import AsyncWebClient

from alert_manager.bot.app import create_client as create_slack_socket_client
from alert_manager.config import Config, FilterBackend
from alert_manager.libs.security import accounts_dep
from alert_manager.logger import init_logger
from alert_manager.services.alert_filter_backend import (
    InMemoryAlertFilter,
    RedisAlertFilter,
)
from alert_manager.web.views import router


async def startup_handler(app: web.Application, config: Config) -> None:
    if config.filter_backend == FilterBackend.redis:
        if config.redis_url is None:
            raise ValueError('Redis url is not set')
        redis_params = {
            **parse_redis_url(config.redis_url),
            'ssl': bool(config.redis_ssl_ca_certs_path),
            'ssl_ca_certs': config.redis_ssl_ca_certs_path,
            'ssl_certfile': config.redis_ssl_client_cert_path,
            'ssl_keyfile': config.redis_ssl_client_key_path,
        }
        app['redis'] = Redis(**redis_params)
        app['alert_filter'] = RedisAlertFilter(app['redis'])
        await app['redis'].ping()
    else:
        app['alert_filter'] = InMemoryAlertFilter()

    app['slack_client'] = AsyncWebClient(token=config.slack_token)
    app['slack_socket_client'] = await create_slack_socket_client(
        app['slack_client'], t.cast(str, config.slack_socket_mode_token), app['alert_filter']
    )


async def shutdown_handler(app: web.Application) -> None:
    if redis := app.get('redis'):
        await redis.aclose()
    await app['slack_socket_client'].close()


def app_factory(config: Config) -> web.Application:
    init_logger(
        log_format=config.log_format.value,
        log_level=config.log_level.value,
        log_timestamp_format=config.log_timestamp_format.value,
        log_health_check_is_enable=config.log_health_check_is_enable,
    )

    if config.sentry_dsn:
        sentry_sdk.init(
            dsn=config.sentry_dsn,
            integrations=[AsyncioIntegration(), AioHttpIntegration()],
            send_default_pii=True,
            ca_certs=config.sentry_ca_certs,
        )

    main_router = Router()
    main_router.add_routes(router, prefix=config.router_prefix)

    app = web.Application()
    app.on_startup.extend((deps_init, setup_swagger(), partial(startup_handler, config=config)))
    app.on_shutdown.append(shutdown_handler)
    app.add_routes(main_router)

    app['values_overrides'] = {accounts_dep: config.accounts}

    return app
