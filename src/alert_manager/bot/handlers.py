import typing as t
from functools import wraps

from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.web.async_client import AsyncWebClient

from alert_manager.services.alert_filter_backend import BaseAlertFilter
from alert_manager.services.slack.exceptions import RuleUrlExtractError
from alert_manager.services.slack.message import MessageBuilder, get_rule_url

T = t.TypeVar('T')
P = t.ParamSpec('P')


def auto_ack(func: t.Callable[P, t.Awaitable[T]]) -> t.Callable[P, t.Awaitable[None]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
        await func(*args, **kwargs)
        await kwargs['client'].send_socket_mode_response(  # type: ignore[attr-defined]
            SocketModeResponse(envelope_id=kwargs['request'].envelope_id)  # type: ignore[attr-defined]
        )

    return wrapper


class Dispatcher:
    def __init__(self, slack_client: AsyncWebClient, alert_filter: BaseAlertFilter) -> None:
        self.slack_client = slack_client
        self.alert_filter: BaseAlertFilter = alert_filter

    async def __call__(self, client: SocketModeClient, request: SocketModeRequest) -> None:
        actions_by_ids = {
            action_obj['action_id']: action_obj for action_obj in request.payload['actions']
        }
        if (
            request.type == 'interactive'
            and request.payload['type'] == 'block_actions'
            and 'snooze-for' in actions_by_ids
        ):
            await self.snooze_handler(
                client=client, request=request, action=actions_by_ids['snooze-for']
            )

    @auto_ack
    async def snooze_handler(
        self, *, client: SocketModeClient, request: SocketModeRequest, action: dict[str, t.Any]
    ) -> None:
        text = request.payload['message']['text']
        blocks = MessageBuilder.add_alert_status_to_message(
            message_blocks=request.payload['message']['blocks'],
            action_data=action,
            snoozed_by=request.payload['user']['username'],
        )

        rule_url = get_rule_url(request.payload['message']['blocks'])
        if not rule_url:
            raise RuleUrlExtractError("Can't extract rule url from source message")

        minutes = int(request.payload['actions'][0]['selected_option']['value'])
        await self.alert_filter.snooze(rule_url, int(minutes))

        await self.slack_client.chat_update(
            channel=request.payload['channel']['id'],
            ts=request.payload['message']['ts'],
            blocks=blocks,
            text=text,
        )
