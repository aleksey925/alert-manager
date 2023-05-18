from aiohttp import web
from aiohttp_deps import init as deps_init
from aiohttp_deps import setup_swagger
from redis.asyncio.client import Redis
from slack_sdk.signature import SignatureVerifier
from slack_sdk.web.async_client import AsyncWebClient

from alert_manager.config import Config, FilterBackend
from alert_manager.logger import init_logger
from alert_manager.services.alert_filter import InMemoryAlertFilter, RedisAlertFilter
from alert_manager.web.middleware import global_error_handler
from alert_manager.web.views import router


async def check_redis_conn(app: web.Application) -> None:
    if app.get('redis'):
        await app['redis'].ping()


async def shutdown_handler(app: web.Application) -> None:
    await app['redis'].close()


def app_factory(config: Config) -> web.Application:
    init_logger(log_format=config.log_format.value, log_level=config.log_level)

    app = web.Application(middlewares=[global_error_handler])
    app.on_startup.extend((deps_init, setup_swagger(), check_redis_conn))
    app.on_shutdown.append(shutdown_handler)
    app.add_routes(router)

    if config.filter_backend == FilterBackend.redis:
        if config.redis_url is None:
            raise ValueError('Redis url is not set')
        app['redis'] = Redis.from_url(config.redis_url)
        app['alert_filter'] = RedisAlertFilter(app['redis'])
    else:
        app['alert_filter'] = InMemoryAlertFilter()

    app['slack_client'] = AsyncWebClient(token=config.slack_token)
    app['slack_signature_verifier'] = SignatureVerifier(signing_secret=config.slack_signing_secret)

    return app
