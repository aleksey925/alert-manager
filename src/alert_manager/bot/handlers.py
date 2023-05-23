import typing as t
from datetime import datetime

from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.web.async_client import AsyncWebClient

from alert_manager.services.alert_filter_backend import BaseAlertFilter
from alert_manager.services.slack.exceptions import RuleUrlExtractError
from alert_manager.services.slack.message import get_rule_url_from_title


class Dispatcher:
    def __init__(self, slack_client: AsyncWebClient, alert_filter: BaseAlertFilter) -> None:
        self.slack_client = slack_client
        self.alert_filter: BaseAlertFilter = alert_filter

    async def __call__(self, client: SocketModeClient, request: SocketModeRequest) -> None:
        if request.type == 'interactive':
            await self.snooze_handler(client, request)

    async def snooze_handler(self, client: SocketModeClient, request: SocketModeRequest) -> None:
        period = request.payload['actions'][0]['selected_option']['text']['text']
        context_block = {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":sleeping: Snoozed at {datetime.utcnow().strftime('%d %B %Y %H:%M:%S') } UTC, for {period}"
                }
            ]
        }

        new_blocks = request.payload['message']['blocks']
        if new_blocks[-1]['type'] == 'context':
            new_blocks.pop()

        if period != 'wake':
            new_blocks.append(context_block)

        await self.slack_client.chat_update(
            channel=request.payload['channel']['id'],
            ts=request.payload['message']['ts'],
            blocks=new_blocks,
        )

        await handle_snooze_action(self.alert_filter, request.payload)
        await client.send_socket_mode_response(SocketModeResponse(envelope_id=request.envelope_id))


async def handle_snooze_action(alert_filter: BaseAlertFilter, payload: dict[str, t.Any]) -> None:
    rule_url = get_rule_url_from_title(payload['message']['blocks'][0]['text']['text'])
    if not rule_url:
        raise RuleUrlExtractError("Can't extract rule url from message title")

    minutes = payload['actions'][0]['selected_option']['value']
    if minutes == 'wake':
        await alert_filter.wake(rule_url)
    else:
        await alert_filter.snooze(rule_url, int(minutes))