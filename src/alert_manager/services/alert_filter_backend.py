from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from redis.asyncio import Redis

from alert_manager.entities.alert_metadata import AlertMetadata
from alert_manager.libs.asyncio_utils import periodic_task


class BaseAlertFilter(ABC):
    def create_key(self, channel: str, rule_url: str) -> str:
        return f'{channel};{rule_url}'

    @abstractmethod
    async def snooze(
        self, channel: str, title: str, rule_url: str, snoozed_by: str, minutes: int
    ) -> None:
        raise NotImplementedError  # pragma: no cover

    async def wake_up(self, key: str) -> None:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    async def is_snoozed(self, channel: str, rule_url: str) -> bool:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    async def get_all(self, channel: str) -> dict[str, AlertMetadata]:
        raise NotImplementedError  # pragma: no cover


class InMemoryAlertFilter(BaseAlertFilter):
    def __init__(self) -> None:
        self._snoozed_alerts: dict[str, AlertMetadata] = {}
        self._periodic_clean_task = periodic_task(self._clean_alerts, 120)

    async def snooze(
        self, channel: str, title: str, rule_url: str, snoozed_by: str, minutes: int
    ) -> None:
        key = self.create_key(channel, rule_url)
        if minutes == 0:
            await self.wake_up(key)
        else:
            self._snoozed_alerts[key] = AlertMetadata(
                title=title,
                rule_url=rule_url,
                snoozed_by=snoozed_by,
                snoozed_until=(datetime.now() + timedelta(minutes=minutes)).timestamp(),
                channel=channel,
            )

    async def wake_up(self, key: str) -> None:
        self._snoozed_alerts.pop(key, '')

    async def is_snoozed(self, channel: str, rule_url: str) -> bool:
        key = self.create_key(channel, rule_url)

        if key not in self._snoozed_alerts:
            return False

        if self._snoozed_alerts[key].snoozed_until > datetime.now().timestamp():
            return True
        else:
            del self._snoozed_alerts[key]

        return False

    async def _clean_alerts(self) -> None:
        current_timestamp = datetime.now().timestamp()
        self._snoozed_alerts = {
            key: metadata
            for key, metadata in self._snoozed_alerts.items()
            if metadata.snoozed_until > current_timestamp
        }

    async def get_all(self, channel: str) -> dict[str, AlertMetadata]:
        return {
            key: metadata
            for key, metadata in self._snoozed_alerts.items()
            if metadata.channel == channel
        }


class RedisAlertFilter(BaseAlertFilter):
    def __init__(self, redis: Redis) -> None:  # type: ignore[type-arg]
        self.redis = redis

    async def snooze(
        self, channel: str, title: str, rule_url: str, snoozed_by: str, minutes: int
    ) -> None:
        key = self.create_key(channel, rule_url)
        if minutes == 0:
            await self.wake_up(key)
        else:
            metadata = AlertMetadata(
                title=title,
                rule_url=rule_url,
                snoozed_by=snoozed_by,
                snoozed_until=(datetime.now() + timedelta(minutes=minutes)).timestamp(),
                channel=channel,
            )
            await self.redis.set(
                key, metadata.model_dump_json(), ex=int(timedelta(minutes=minutes).total_seconds())
            )

    async def wake_up(self, key: str) -> None:
        await self.redis.delete(key)

    async def is_snoozed(self, channel: str, rule_url: str) -> bool:
        key = self.create_key(channel, rule_url)
        return bool(await self.redis.exists(key))

    async def get_all(self, channel: str) -> dict[str, AlertMetadata]:
        keys = [i.decode() for i in await self.redis.keys(f'{channel};*')]
        return {
            key: AlertMetadata.model_validate_json(raw_metadata)
            for key, raw_metadata in zip(keys, await self.redis.mget(keys), strict=True)
            if raw_metadata
        }
