from datetime import datetime, timedelta

import pytest
from alert_manager.entities.alert_metadata import AlertMetadata
from alert_manager.services.alert_filter_backend import (
    InMemoryAlertFilter,
    RedisAlertFilter,
)
from fakeredis import aioredis
from freezegun import freeze_time


@freeze_time('2023-07-11')
class TestInMemoryAlertFilter:
    async def test_snooze(self, alert_filter, alert_metadata, alert_key):
        # arrange
        minutes = int((alert_metadata.snoozed_until - datetime.now().timestamp()) / 60)

        # act
        await alert_filter.snooze(
            channel_name=alert_metadata.channel_name,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=minutes,
        )

        # assert
        assert alert_key in alert_filter._snoozed_alerts
        assert alert_filter._snoozed_alerts[alert_key] == alert_metadata

    async def test_snooze__snooze_to_zero_minutes__alert_deleted_from_inner_storage(
        self, alert_filter, alert_metadata, alert_key
    ):
        # arrange
        alert_filter._snoozed_alerts[alert_key] = alert_metadata

        # act
        await alert_filter.snooze(
            channel_name=alert_metadata.channel_name,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=0,
        )

        # assert
        assert alert_key not in alert_filter._snoozed_alerts
        assert (
            await alert_filter.is_snoozed(
                channel_name=alert_metadata.channel_name,
                rule_url=alert_metadata.rule_url,
            )
            is False
        )

    async def test_is_snoozed(self, alert_filter, alert_metadata, alert_key):
        # arrange
        alert_filter._snoozed_alerts[alert_key] = alert_metadata

        # act
        result = await alert_filter.is_snoozed(
            channel_name=alert_metadata.channel_name, rule_url=alert_metadata.rule_url
        )

        # assert
        assert result is True

    async def test_is_snoozed__inner_storage_is_empty__return_false(
        self, alert_filter, alert_metadata
    ):
        # act
        result = await alert_filter.is_snoozed(
            channel_name=alert_metadata.channel_name, rule_url=alert_metadata.rule_url
        )

        # assert
        assert result is False

    async def test_is_snoozed__check_expired_alert(self, alert_filter, alert_metadata, alert_key):
        # arrange
        snoozed_until = (datetime.now() - timedelta(minutes=10)).timestamp()
        alert_metadata.snoozed_until = snoozed_until
        alert_filter._snoozed_alerts[alert_key] = alert_metadata

        # act
        result = await alert_filter.is_snoozed(
            channel_name=alert_metadata.channel_name, rule_url=alert_metadata.rule_url
        )

        # assert
        assert result is False

    async def test_clean_alerts(self, alert_filter, alert_metadata, alert_key):
        # arrange
        snoozed_until = (datetime.now() - timedelta(minutes=10)).timestamp()
        alert_metadata.snoozed_until = snoozed_until
        alert_filter._snoozed_alerts[alert_key] = alert_metadata

        # act
        await alert_filter._clean_alerts()

        # assert
        assert alert_key not in alert_filter._snoozed_alerts

    async def test_get_all(self, alert_filter, alert_metadata, alert_key):
        # arrange
        alert_filter._snoozed_alerts[alert_key] = alert_metadata

        # act
        alerts = await alert_filter.get_all(channel_name=alert_metadata.channel_name)

        # assert
        assert alerts == {alert_key: alert_metadata}

    async def test_get_all__get_non_existent_alerts__receive_empty_dict(
        self, alert_filter, alert_metadata, alert_key
    ):
        # arrange
        alert_filter._snoozed_alerts[alert_key] = alert_metadata

        # act
        alerts = await alert_filter.get_all(channel_name='some_channel')

        # assert
        assert alerts == {}

    @pytest.fixture(name='alert_filter', autouse=True)
    async def alert_filter_fixture(self):
        alert_filter = InMemoryAlertFilter()
        yield alert_filter
        alert_filter._periodic_clean_task.cancel()


@freeze_time('2023-07-11')
class TestRedisAlertFilter:
    async def test_snooze(self, fake_redis, alert_filter, alert_metadata, alert_key):
        # arrange
        minutes = int((alert_metadata.snoozed_until - datetime.now().timestamp()) / 60)

        # act
        await alert_filter.snooze(
            channel_name=alert_metadata.channel_name,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=minutes,
        )

        # assert
        alerts = await fake_redis.mget(alert_key)
        assert len(alerts) == 1
        assert AlertMetadata.parse_raw(alerts[0]) == alert_metadata

    async def test_snooze__snooze_to_zero_minutes__alert_deleted_from_inner_storage(
        self, fake_redis, alert_filter, alert_metadata, alert_key
    ):
        # arrange
        await alert_filter.snooze(
            channel_name=alert_metadata.channel_name,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=10,
        )

        # act
        await alert_filter.snooze(
            channel_name=alert_metadata.channel_name,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=0,
        )

        # assert
        alerts = await fake_redis.mget(alert_key)
        assert alerts == [None]
        assert (
            await alert_filter.is_snoozed(
                channel_name=alert_metadata.channel_name,
                rule_url=alert_metadata.rule_url,
            )
            is False
        )

    async def test_is_snoozed(self, alert_filter, alert_metadata, alert_key):
        # arrange
        await alert_filter.snooze(
            channel_name=alert_metadata.channel_name,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=10,
        )

        # act
        result = await alert_filter.is_snoozed(
            channel_name=alert_metadata.channel_name, rule_url=alert_metadata.rule_url
        )

        # assert
        assert result is True

    async def test_is_snoozed__inner_storage_is_empty__return_false(
        self, alert_filter, alert_metadata
    ):
        # act
        result = await alert_filter.is_snoozed(
            channel_name=alert_metadata.channel_name, rule_url=alert_metadata.rule_url
        )

        # assert
        assert result is False

    async def test_is_snoozed__check_expired_alert(self, alert_filter, alert_metadata, alert_key):
        # arrange
        with freeze_time('2023-07-10'):
            await alert_filter.snooze(
                channel_name=alert_metadata.channel_name,
                title=alert_metadata.title,
                rule_url=alert_metadata.rule_url,
                snoozed_by=alert_metadata.snoozed_by,
                minutes=10,
            )

        # act
        result = await alert_filter.is_snoozed(
            channel_name=alert_metadata.channel_name, rule_url=alert_metadata.rule_url
        )

        # assert
        assert result is False

    async def test_get_all(self, alert_filter, alert_metadata, alert_key):
        # arrange
        await alert_filter.snooze(
            channel_name=alert_metadata.channel_name,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=10,
        )

        # act
        alerts = await alert_filter.get_all(channel_name=alert_metadata.channel_name)

        # assert
        assert alerts == {alert_key: alert_metadata}

    async def test_get_all__get_non_existent_alerts__receive_empty_dict(
        self, alert_filter, alert_metadata, alert_key
    ):
        # arrange
        await alert_filter.snooze(
            channel_name=alert_metadata.channel_name,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by=alert_metadata.snoozed_by,
            minutes=10,
        )

        # act
        alerts = await alert_filter.get_all(channel_name='some_channel')

        # assert
        assert alerts == {}

    @pytest.fixture
    def fake_redis(self):
        return aioredis.FakeRedis(version=(6,))

    @pytest.fixture(name='alert_filter', autouse=True)
    async def alert_filter_fixture(self, fake_redis):
        return RedisAlertFilter(fake_redis)


@pytest.fixture(name='alert_metadata')
@freeze_time('2023-07-11')
def alert_metadata_fixture():
    return AlertMetadata(
        channel_name='channel1',
        title='[Alerting] Alert title',
        snoozed_by='user_nick',
        snoozed_until=(datetime.now() + timedelta(minutes=10)).timestamp(),
        rule_url='rule1',
    )


@pytest.fixture(name='alert_key')
def alert_key_fixture(alert_metadata: AlertMetadata):
    return f'{alert_metadata.channel_name};{alert_metadata.rule_url}'
