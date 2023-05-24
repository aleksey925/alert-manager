from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from redis.asyncio import Redis

from alert_manager.libs.asyncio_utils import periodic_task


class BaseAlertFilter(ABC):
    @abstractmethod
    async def snooze(self, rule_url: str, minutes: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def is_snoozed(self, rule_url: str) -> bool:
        raise NotImplementedError


class InMemoryAlertFilter(BaseAlertFilter):
    def __init__(self) -> None:
        self._snoozed_alerts: dict[str, int | float] = {}
        self._periodic_clean_task = periodic_task(self._clean_alerts, 120)

    async def snooze(self, rule_url: str, minutes: int) -> None:
        if minutes == 0:
            self._snoozed_alerts.pop(rule_url, '')
        else:
            self._snoozed_alerts[rule_url] = (
                datetime.now() + timedelta(minutes=minutes)
            ).timestamp()

    async def is_snoozed(self, rule_url: str) -> bool:
        if rule_url not in self._snoozed_alerts:
            return False

        if self._snoozed_alerts[rule_url] > datetime.now().timestamp():
            return True
        else:
            del self._snoozed_alerts[rule_url]

        return False

    async def _clean_alerts(self) -> None:
        current_timestamp = datetime.now().timestamp()
        self._snoozed_alerts = {
            url: timestamp
            for url, timestamp in self._snoozed_alerts.items()
            if timestamp > current_timestamp
        }


class RedisAlertFilter(BaseAlertFilter):
    def __init__(self, redis: Redis) -> None:  # type: ignore[type-arg]
        self.redis = redis

    async def snooze(self, rule_url: str, minutes: int) -> None:
        if minutes == 0:
            await self.redis.delete(rule_url)
        else:
            await self.redis.set(rule_url, '', ex=int(timedelta(minutes=minutes).total_seconds()))

    async def is_snoozed(self, rule_url: str) -> bool:
        return bool(await self.redis.exists(rule_url))
