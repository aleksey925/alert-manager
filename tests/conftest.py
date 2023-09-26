from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fakeredis import aioredis
from freezegun import freeze_time
from pytest_aiohttp.plugin import AiohttpClient
from pytest_mock import MockFixture
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.web.async_client import AsyncWebClient

from alert_manager.config import Config
from alert_manager.entities.alert_metadata import AlertMetadata
from alert_manager.main import app_factory
from alert_manager.services.alert_filter_backend import RedisAlertFilter
from tests.fixtures import *  # noqa: F403


@pytest.fixture(name='test_dir')
def test_dir_fixture():
    return Path(__file__).absolute().parent


@pytest.fixture(name='config')
def config_fixture():
    class ConfigMock(Config):
        @classmethod
        def settings_customise_sources(cls, settings_cls, init_settings, *args, **kwargs):
            return (init_settings,)

    return ConfigMock(
        slack_token='slack_token', slack_socket_mode_token='slack_socket_mode_token', accounts='{}'
    )


@pytest.fixture(name='redis')
async def redis_fixture():
    inst = aioredis.FakeRedis(version=(6,))
    yield inst
    await inst.flushall()


@pytest.fixture(name='alert_filter')
async def alert_filter_fixture(redis) -> RedisAlertFilter:
    return RedisAlertFilter(redis)


@pytest.fixture(name='slack_client')
def slack_client_fixture(mocker: MockFixture):
    return mocker.MagicMock(AsyncWebClient)


@pytest.fixture(name='slack_socket_client')
def slack_socket_client_fixture(mocker: MockFixture):
    return mocker.MagicMock(SocketModeClient)


@pytest.fixture(name='app')
async def app_fixture(
    mocker: MockFixture, config, redis, alert_filter, slack_client, slack_socket_client
):
    mocker.patch('alert_manager.main.startup_handler')
    app = app_factory(config)
    app['redis'] = redis
    app['alert_filter'] = alert_filter
    app['slack_client'] = slack_client
    app['slack_socket_client'] = slack_socket_client
    yield app


@pytest.fixture
async def client(aiohttp_client, app) -> AiohttpClient:
    return await aiohttp_client(app)


@pytest.fixture(name='channel')
def channel_fixture():
    return 'alerts'


@pytest.fixture(name='webhook_url')
def webhook_url_fixture(channel):
    return f'/webhook/grafana/?channel={channel}'


@pytest.fixture(name='alert_metadata')
@freeze_time('2023-07-11')
def alert_metadata_fixture(channel, legacy_alert_alerting_value_int):
    return AlertMetadata(
        channel_name=channel,
        title=legacy_alert_alerting_value_int['title'],
        snoozed_by='user_nick',
        snoozed_until=(datetime.now() + timedelta(minutes=10)).timestamp(),
        rule_url=legacy_alert_alerting_value_int['ruleUrl'],
    )
