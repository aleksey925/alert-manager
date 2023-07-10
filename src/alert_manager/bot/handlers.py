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
        if request.type == 'interactive':
            await self._dispatch_actions(client=client, request=request)

        if request.type == 'slash_commands':
            await self._dispatch_commands(client=client, request=request)

    async def _dispatch_actions(
        self, *, client: SocketModeClient, request: SocketModeRequest
    ) -> None:
        if request.payload['type'] != 'block_actions':
            return

        actions_by_ids = {
            action_obj['action_id']: action_obj for action_obj in request.payload['actions']
        }
        if 'snooze-for' in actions_by_ids:
            await self.snooze_handler(
                client=client, request=request, action=actions_by_ids['snooze-for']
            )
        if 'wake-up' in actions_by_ids:
            await self.wake_up_handler(
                client=client, request=request, action=actions_by_ids['wake-up']
            )

    async def _dispatch_commands(
        self, *, client: SocketModeClient, request: SocketModeRequest
    ) -> None:
        if request.payload['command'] == '/get-snoozed-alerts':
            await self.get_snoozed_alerts_handler(client=client, request=request)

    @auto_ack
    async def snooze_handler(
        self, *, client: SocketModeClient, request: SocketModeRequest, action: dict[str, t.Any]
    ) -> None:
        snoozed_by: str = request.payload['user']['username']
        title = request.payload['message']['text']
        blocks = MessageBuilder.add_alert_status_to_message(
            message_blocks=request.payload['message']['blocks'],
            action_data=action,
            snoozed_by=snoozed_by,
        )

        channel_name: str = request.payload['channel']['name']
        rule_url = get_rule_url(request.payload['message']['blocks'])
        if not rule_url:
            raise RuleUrlExtractError("Can't extract rule url from source message")

        minutes = int(request.payload['actions'][0]['selected_option']['value'])
        await self.alert_filter.snooze(
            channel_name=channel_name,
            title=title,
            rule_url=rule_url,
            snoozed_by=snoozed_by,
            minutes=int(minutes),
        )

        await self.slack_client.chat_update(
            channel=request.payload['channel']['id'],
            ts=request.payload['message']['ts'],
            blocks=blocks,
            text=title,
        )

    @auto_ack
    async def wake_up_handler(
        self, *, client: SocketModeClient, request: SocketModeRequest, action: dict[str, t.Any]
    ) -> None:
        alert_key = action['value']
        await self.alert_filter.wake_up(alert_key)

        text = request.payload['message']['text']
        blocks = MessageBuilder.remove_woke_alert(
            message_blocks=request.payload['message']['blocks'], alert_key=alert_key
        )
        await self.slack_client.chat_update(
            channel=request.payload['channel']['id'],
            ts=request.payload['message']['ts'],
            blocks=blocks,
            text=text,
        )

    @auto_ack
    async def get_snoozed_alerts_handler(
        self, *, client: SocketModeClient, request: SocketModeRequest
    ) -> None:
        snoozed_alerts = await self.alert_filter.get_all(request.payload['channel_name'])
        text, blocks = MessageBuilder.create_list_snoozed_alerts(snoozed_alerts)
        await self.slack_client.chat_postMessage(
            channel=request.payload['channel_id'],
            user=request.payload['user_id'],
            blocks=blocks,
            text=text,
        )
