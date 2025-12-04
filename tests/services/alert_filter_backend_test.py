from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

from alert_manager.entities.alert_metadata import AlertMetadata
from alert_manager.services.alert_filter_backend import (
    InMemoryAlertFilter,
    RedisAlertFilter,
)


@freeze_time('2023-07-11')
class TestInMemoryAlertFilter:
    async def test_snooze(self, in_memory_alert_filter, alert_metadata, alert_key):
        # arrange
        minutes = int((alert_metadata.snoozed_until - datetime.now().timestamp()) / 60)

        # act
        await in_memory_alert_filter.snooze(
            channel=alert_metadata.channel,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=minutes,
        )

        # assert
        assert alert_key in in_memory_alert_filter._snoozed_alerts
        assert in_memory_alert_filter._snoozed_alerts[alert_key] == alert_metadata

    async def test_snooze__snooze_to_zero_minutes__alert_deleted_from_inner_storage(
        self, in_memory_alert_filter, alert_metadata, alert_key
    ):
        # arrange
        in_memory_alert_filter._snoozed_alerts[alert_key] = alert_metadata

        # act
        await in_memory_alert_filter.snooze(
            channel=alert_metadata.channel,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=0,
        )

        # assert
        assert alert_key not in in_memory_alert_filter._snoozed_alerts
        assert (
            await in_memory_alert_filter.is_snoozed(
                channel=alert_metadata.channel,
                rule_url=alert_metadata.rule_url,
            )
            is False
        )

    async def test_is_snoozed(self, in_memory_alert_filter, alert_metadata, alert_key):
        # arrange
        in_memory_alert_filter._snoozed_alerts[alert_key] = alert_metadata

        # act
        result = await in_memory_alert_filter.is_snoozed(
            channel=alert_metadata.channel, rule_url=alert_metadata.rule_url
        )

        # assert
        assert result is True

    async def test_is_snoozed__inner_storage_is_empty__return_false(self, in_memory_alert_filter, alert_metadata):
        # act
        result = await in_memory_alert_filter.is_snoozed(
            channel=alert_metadata.channel, rule_url=alert_metadata.rule_url
        )

        # assert
        assert result is False

    async def test_is_snoozed__check_expired_alert(self, in_memory_alert_filter, alert_metadata, alert_key):
        # arrange
        snoozed_until = (datetime.now() - timedelta(minutes=10)).timestamp()
        alert_metadata.snoozed_until = snoozed_until
        in_memory_alert_filter._snoozed_alerts[alert_key] = alert_metadata

        # act
        result = await in_memory_alert_filter.is_snoozed(
            channel=alert_metadata.channel, rule_url=alert_metadata.rule_url
        )

        # assert
        assert result is False

    async def test_clean_alerts(self, in_memory_alert_filter, alert_metadata, alert_key):
        # arrange
        snoozed_until = (datetime.now() - timedelta(minutes=10)).timestamp()
        alert_metadata.snoozed_until = snoozed_until
        in_memory_alert_filter._snoozed_alerts[alert_key] = alert_metadata

        # act
        await in_memory_alert_filter._clean_alerts()

        # assert
        assert alert_key not in in_memory_alert_filter._snoozed_alerts

    async def test_get_all(self, in_memory_alert_filter, alert_metadata, alert_key):
        # arrange
        in_memory_alert_filter._snoozed_alerts[alert_key] = alert_metadata

        # act
        alerts = await in_memory_alert_filter.get_all(channel=alert_metadata.channel)

        # assert
        assert alerts == {alert_key: alert_metadata}

    async def test_get_all__get_non_existent_alerts__receive_empty_dict(
        self, in_memory_alert_filter, alert_metadata, alert_key
    ):
        # arrange
        in_memory_alert_filter._snoozed_alerts[alert_key] = alert_metadata

        # act
        alerts = await in_memory_alert_filter.get_all(channel='some_channel')

        # assert
        assert alerts == {}


@freeze_time('2023-07-11')
class TestRedisAlertFilter:
    async def test_snooze(self, redis, redis_alert_filter, alert_metadata, alert_key):
        # arrange
        minutes = int((alert_metadata.snoozed_until - datetime.now().timestamp()) / 60)

        # act
        await redis_alert_filter.snooze(
            channel=alert_metadata.channel,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=minutes,
        )

        # assert
        alerts = await redis.mget(alert_key)
        assert len(alerts) == 1
        assert AlertMetadata.model_validate_json(alerts[0]) == alert_metadata

    async def test_snooze__snooze_to_zero_minutes__alert_deleted_from_inner_storage(
        self, redis, redis_alert_filter, alert_metadata, alert_key
    ):
        # arrange
        await redis_alert_filter.snooze(
            channel=alert_metadata.channel,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=10,
        )

        # act
        await redis_alert_filter.snooze(
            channel=alert_metadata.channel,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=0,
        )

        # assert
        alerts = await redis.mget(alert_key)
        assert alerts == [None]
        assert (
            await redis_alert_filter.is_snoozed(
                channel=alert_metadata.channel,
                rule_url=alert_metadata.rule_url,
            )
            is False
        )

    async def test_is_snoozed(self, redis_alert_filter, alert_metadata, alert_key):
        # arrange
        await redis_alert_filter.snooze(
            channel=alert_metadata.channel,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=10,
        )

        # act
        result = await redis_alert_filter.is_snoozed(channel=alert_metadata.channel, rule_url=alert_metadata.rule_url)

        # assert
        assert result is True

    async def test_is_snoozed__inner_storage_is_empty__return_false(self, redis_alert_filter, alert_metadata):
        # act
        result = await redis_alert_filter.is_snoozed(channel=alert_metadata.channel, rule_url=alert_metadata.rule_url)

        # assert
        assert result is False

    async def test_is_snoozed__check_expired_alert(self, redis_alert_filter, alert_metadata, alert_key):
        # arrange
        with freeze_time('2023-07-10'):
            await redis_alert_filter.snooze(
                channel=alert_metadata.channel,
                title=alert_metadata.title,
                rule_url=alert_metadata.rule_url,
                snoozed_by=alert_metadata.snoozed_by,
                minutes=10,
            )

        # act
        result = await redis_alert_filter.is_snoozed(channel=alert_metadata.channel, rule_url=alert_metadata.rule_url)

        # assert
        assert result is False

    async def test_get_all(self, redis_alert_filter, alert_metadata, alert_key):
        # arrange
        await redis_alert_filter.snooze(
            channel=alert_metadata.channel,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=10,
        )

        # act
        alerts = await redis_alert_filter.get_all(channel=alert_metadata.channel)

        # assert
        assert alerts == {alert_key: alert_metadata}

    async def test_get_all__get_non_existent_alerts__receive_empty_dict(
        self, redis_alert_filter, alert_metadata, alert_key
    ):
        # arrange
        await redis_alert_filter.snooze(
            channel=alert_metadata.channel,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=10,
        )

        # act
        alerts = await redis_alert_filter.get_all(channel='some_channel')

        # assert
        assert alerts == {}


@pytest.fixture(name='redis_alert_filter')
async def redis_alert_filter_fixture(redis):
    return RedisAlertFilter(redis)


@pytest.fixture(name='in_memory_alert_filter')
async def in_memory_alert_filter_fixture():
    alert_filter = InMemoryAlertFilter()
    yield alert_filter
    alert_filter._periodic_clean_task.cancel()


@pytest.fixture(name='alert_key')
def alert_key_fixture(channel, alert_metadata: AlertMetadata):
    return f'{channel};{alert_metadata.rule_url}'
