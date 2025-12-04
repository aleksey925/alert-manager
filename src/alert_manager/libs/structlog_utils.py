import time
import typing as t

from structlog.processors import TimeStamper as _TimeStamper
from structlog.typing import EventDict


class TimeStamper(_TimeStamper):
    fmt_mapping: t.ClassVar[dict[str | None, None]] = {'unix': None}

    def __init__(
        self,
        fmt: str | None = None,
        utc: bool = True,
        key: str = 'timestamp',
    ) -> None:
        super().__init__(self.fmt_mapping.get(fmt, fmt), utc, key)

        if fmt == 'unix_ms':
            self._stamper = self._make_unix_ms_stamper()

    def _make_unix_ms_stamper(self) -> t.Callable[[EventDict], EventDict]:
        key = self.key

        def stamper_unix_ms(event_dict: EventDict) -> EventDict:
            event_dict[key] = time.time() * 1000
            return event_dict

        return stamper_unix_ms
