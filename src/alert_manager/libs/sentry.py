from typing import Any, Literal

from sentry_sdk import capture_message as _capture_message
from sentry_sdk import new_scope


def capture_message(
    message: str, level: Literal['fatal', 'critical', 'error', 'warning', 'info', 'debug'], extra: dict[str, Any]
) -> None:
    with new_scope() as scope:
        for key, value in extra.items():
            scope.set_extra(key, value)
        _capture_message(message, level=level, scope=scope)
