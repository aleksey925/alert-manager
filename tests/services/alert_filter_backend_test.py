from datetime import datetime, timedelta

import pytest
from alert_manager.services.alert_filter_backend import InMemoryAlertFilter


class TestInMemoryAlertFilter:
    @pytest.fixture(name='alert_filter', autouse=True)
    async def alert_filter_fixture(self):
        alert_filter = InMemoryAlertFilter()
        yield alert_filter
        alert_filter._periodic_clean_task.cancel()

    async def test_snooze(self, alert_filter):
        # arrange
        now = datetime.now()
        minutes = 10
        rule_url = 'rule1'

        # act
        await alert_filter.snooze(rule_url, minutes)

        # assert
        assert rule_url in alert_filter._snoozed_alerts
        assert int(alert_filter._snoozed_alerts[rule_url]) == int(
            (now + timedelta(minutes=minutes)).timestamp()
        )

    async def test_snooze__snooze_to_zero_minutes__alert_deleted_from_inner_storage(
        self, alert_filter
    ):
        # arrange
        rule_url = 'rule1'
        await alert_filter.snooze(rule_url, 10)

        # act
        await alert_filter.snooze(rule_url, 0)

        # assert
        assert rule_url not in alert_filter._snoozed_alerts

    async def test_is_snoozed(self, alert_filter):
        # arrange
        now = datetime.now()
        minutes = 10
        rule_url = 'rule1'
        snooze_time = (now + timedelta(minutes=minutes)).timestamp()
        alert_filter._snoozed_alerts[rule_url] = snooze_time

        # act
        result = await alert_filter.is_snoozed(rule_url)

        # assert
        assert result is True

    async def test_is_snoozed__inner_storage_is_empty__return_false(self, alert_filter):
        # act
        result = await alert_filter.is_snoozed('rule1')

        # assert
        assert result is False

    async def test_is_snoozed__check_expired_alert(self, alert_filter):
        # arrange
        now = datetime.now()
        minutes = 10
        rule_url = 'rule1'
        snooze_time = (now - timedelta(minutes=minutes)).timestamp()
        alert_filter._snoozed_alerts[rule_url] = snooze_time

        # act
        result = await alert_filter.is_snoozed(rule_url)

        # assert
        assert result is False

    async def test_clean_alerts(self, alert_filter):
        # arrange
        now = datetime.now()
        minutes = 10
        rule_url = 'rule1'
        snooze_time = (now - timedelta(minutes=minutes)).timestamp()
        alert_filter._snoozed_alerts[rule_url] = snooze_time

        # act
        await alert_filter._clean_alerts()

        # assert
        assert rule_url not in alert_filter._snoozed_alerts
