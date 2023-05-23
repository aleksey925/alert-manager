import copy
import typing as t
from datetime import datetime
from typing import Any

from alert_manager.enums.grafana import GrafanaAlertState
from alert_manager.web.entities.grafana import GrafanaAlertRequest

MsgBlocksType = list[dict[str, Any]]


def build_alert_message(alert: GrafanaAlertRequest) -> tuple[str, MsgBlocksType]:
    title = alert.title
    rule_url = alert.rule_url

    title_block = {
        'type': 'section',
        'block_id': f'title|{rule_url}',
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
                'action_id': 'snooze-for',
                'placeholder': {
                    'type': 'plain_text',
                    'text': 'Snooze for :sleeping:',
                    'emoji': True,
                },
                'options': [
                    {
                        'text': {'type': 'plain_text', 'text': 'wake'},
                        'value': '0',
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


def get_rule_url(message_blocks: MsgBlocksType) -> str:
    url = ''
    for block in message_blocks:
        if block.get('block_id', '').startswith('title'):
            url = block['block_id'].split('|')[1]
            break

    return url


class MessageBuilder:
    @classmethod
    def add_alert_status_to_message(
        cls, message_blocks: MsgBlocksType, action_data: dict[str, t.Any]
    ) -> MsgBlocksType:
        message_blocks = copy.deepcopy(message_blocks)

        now = datetime.utcnow().strftime('%d %B %Y %H:%M:%S')
        period = action_data['selected_option']['text']['text']

        if message_blocks[-1].get('block_id') == 'alert-status':
            message_blocks.pop()
        if period != 'wake':
            message_blocks.append(
                cls._generate_alert_status_block(now=now, period=period),
            )

        return message_blocks

    @staticmethod
    def _generate_alert_status_block(now: str, period: str) -> dict[str, t.Any]:
        return {
            'type': 'context',
            'block_id': 'alert-status',
            'elements': [
                {
                    'type': 'mrkdwn',
                    'text': f":sleeping: Snoozed at {now} UTC, for {period}",
                }
            ],
        }
