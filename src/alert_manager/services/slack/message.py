import logging
import re
from typing import Any

from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from alert_manager.enums.grafana import GrafanaAlertState
from alert_manager.web.entities.grafana import GrafanaAlertRequest

logger = logging.getLogger(__name__)

MsgBlocksType = list[dict[str, Any]]


def build_alert_message(alert: GrafanaAlertRequest) -> tuple[str, MsgBlocksType]:
    title = alert.title
    rule_url = alert.rule_url

    title_block = {
        'type': 'section',
        'text': {'type': 'mrkdwn', 'text': f'<{rule_url}|*{title}*>'},
    }
    message_block = {'type': 'section', 'text': {'type': 'mrkdwn', 'text': alert.message}}
    eval_matches_block = {
        'type': 'section',
        'fields': [
            {'type': 'mrkdwn', 'text': f'*{match.metric}:* {match.value}'}
            for match in alert.eval_matches
        ],
    }
    snooze_time_select_block = {
        'type': 'actions',
        'elements': [
            {
                'type': 'static_select',
                'action_id': 'snooze-for-action',
                'placeholder': {
                    'type': 'plain_text',
                    'text': 'Snooze for :sleeping:',
                    'emoji': True,
                },
                'options': [
                    {
                        'text': {'type': 'plain_text', 'text': 'wake'},
                        'value': 'wake',
                    },
                    {
                        'text': {'type': 'plain_text', 'text': '1 min'},
                        'value': '1',
                    },
                    {
                        'text': {'type': 'plain_text', 'text': '15 min'},
                        'value': '15',
                    },
                    {
                        'text': {'type': 'plain_text', 'text': '30 min'},
                        'value': '30',
                    },
                    {
                        'text': {'type': 'plain_text', 'text': '1 hour'},
                        'value': '60',
                    },
                    {
                        'text': {'type': 'plain_text', 'text': '2 hours'},
                        'value': '120',
                    },
                    {
                        'text': {'type': 'plain_text', 'text': '5 hours'},
                        'value': '120',
                    },
                    {
                        'text': {'type': 'plain_text', 'text': '1 day'},
                        'value': '1440',
                    },
                ],
            }
        ],
    }

    blocks: MsgBlocksType
    if alert.state is GrafanaAlertState.ok:
        blocks = [title_block]
    else:
        blocks = [
            title_block,
            *((message_block,) if alert.message else ()),
            *((eval_matches_block,) if eval_matches_block['fields'] else ()),
            snooze_time_select_block,
        ]

    return title, blocks


async def post_alert(
    client: AsyncWebClient, text: str, blocks: MsgBlocksType, channel: str
) -> None:
    try:
        await client.chat_postMessage(
            channel=f'#{channel}',
            text=text,
            blocks=blocks,
        )
    except SlackApiError:
        logger.error("Can't post message to slack channel", exc_info=True)
        raise


def get_rule_url_from_title(title: str) -> str:
    match = re.search(r'<([^|>]+)\|[^>]+>', title)
    if match:
        return match.group(1).replace('amp;', '')
    return ''
