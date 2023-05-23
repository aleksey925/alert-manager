import typing as t
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


def get_rule_url(message_blocks: list[dict[str, t.Any]]) -> str:
    url = ''
    for block in message_blocks:
        if block.get('block_id', '').startswith('title'):
            url = block['block_id'].split('|')[1]
            break

    return url
