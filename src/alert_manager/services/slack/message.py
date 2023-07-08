import copy
import typing as t
from datetime import datetime
from typing import Any

from slack_sdk.socket_mode.request import SocketModeRequest

from alert_manager.enums.grafana import GrafanaAlertState
from alert_manager.web.entities.grafana import EvalMatch

MsgBlocksType = list[dict[str, Any]]


def get_rule_url(message_blocks: MsgBlocksType) -> str:
    url = ''
    for block in message_blocks:
        if block.get('block_id', '').startswith('title'):
            url = block['block_id'].split('|')[1]
            break

    return url


class MessageBuilder:
    status_emoji: t.ClassVar[dict[GrafanaAlertState, str]] = {
        GrafanaAlertState.ok: ':large_green_circle:',
        GrafanaAlertState.alerting: ':red_circle:',
        GrafanaAlertState.no_data: ':white_circle:',
    }

    @classmethod
    def create_alert_message(
        cls,
        state: GrafanaAlertState,
        title: str,
        rule_url: str,
        message: str | None,
        eval_matches: list[EvalMatch],
    ) -> tuple[str, MsgBlocksType]:
        status_emoji = f'{cls.status_emoji.get(state, "")} '

        title_block = {
            'type': 'section',
            'block_id': f'title|{rule_url}',
            'text': {'type': 'mrkdwn', 'text': f'{status_emoji}<{rule_url}|*{title}*>'},
        }
        message_block: dict[str, t.Any] = {
            'type': 'section',
            'text': {'type': 'mrkdwn', 'text': message},
            'fields': [
                {'type': 'mrkdwn', 'text': f'*{match.metric}:* {match.value}'}
                for match in eval_matches
            ],
        }
        if not message_block['text']['text']:
            message_block.pop('text')
        if not message_block['fields']:
            message_block.pop('fields')

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
                        {'text': {'type': 'plain_text', 'text': text}, 'value': value}
                        for text, value in [
                            ('wake', '0'),
                            ('15 min', '15'),
                            ('30 min', '30'),
                            ('1 hour', '60'),
                            ('2 hours', '120'),
                            ('5 hours', '300'),
                            ('1 day', '1440'),
                        ]
                    ],
                }
            ],
        }

        blocks: MsgBlocksType
        if state is GrafanaAlertState.ok:
            blocks = [title_block]
        else:
            blocks = [
                title_block,
                message_block,
                snooze_time_select_block,
            ]

        return title, blocks

    @classmethod
    def add_alert_status_to_message(
        cls,
        message_blocks: MsgBlocksType,
        action_data: dict[str, t.Any],
        snoozed_by: str,
    ) -> MsgBlocksType:
        message_blocks = copy.deepcopy(message_blocks)

        now = datetime.utcnow().strftime('%d %B %Y %H:%M:%S')
        period = action_data['selected_option']['text']['text']

        if message_blocks[-1].get('block_id') == 'alert-status':
            message_blocks.pop()
        if period != 'wake':
            message_blocks.append(
                cls._generate_alert_status_block(now=now, period=period, profile_link=snoozed_by)
            )

        return message_blocks

    @staticmethod
    def _generate_alert_status_block(now: str, period: str, profile_link: str) -> dict[str, t.Any]:
        return {
            'type': 'context',
            'block_id': 'alert-status',
            'elements': [
                {
                    'type': 'mrkdwn',
                    'text': f':sleeping: Snoozed at {now} UTC, for {period}, snoozed by <{profile_link}|user>',
                }
            ],
        }

    @classmethod
    def create_user_link(cls, request: SocketModeRequest) -> str:
        return f'https://{request.payload["team"]["domain"]}.slack.com/team/{request.payload["user"]["id"]}'
