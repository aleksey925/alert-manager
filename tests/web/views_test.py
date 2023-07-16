import pytest
from aiohttp.helpers import BasicAuth
from pytest_aiohttp.plugin import AiohttpClient


class TestGrafanaAlertViewLegacyAlert:
    @pytest.mark.parametrize('alert_type', ['alerting', 'no_data'])
    async def test_new_alert_received__message_published(
        self,
        client: AiohttpClient,
        slack_client,
        legacy_alert_alerting,
        legacy_alert_no_data,
        webhook_url,
        channel,
        alert_type,
    ):
        # arrange
        _alert_values = {
            'fields': [
                {
                    'type': 'mrkdwn',
                    'text': f'*{legacy_alert_alerting["evalMatches"][0]["metric"]}:* {legacy_alert_alerting["evalMatches"][0]["value"]}',
                }
            ]
        }
        alert_data, alert_state, circle, alert_values = {
            'alerting': (legacy_alert_alerting, 'Alerting', ':red_circle:', _alert_values),
            'no_data': (legacy_alert_no_data, 'No Data', ':white_circle:', {}),
        }[alert_type]

        # act
        resp = await client.post(webhook_url, json=alert_data)

        # assert
        assert resp.status == 200
        assert await resp.text() == ''
        assert slack_client.chat_postMessage.call_count == 1
        assert slack_client.chat_postMessage.call_args[1] == {
            'channel': f'#{channel}',
            'text': f'[{alert_state}] {legacy_alert_alerting["ruleName"]}',
            'blocks': [
                {
                    'type': 'section',
                    'block_id': f'title|{legacy_alert_alerting["ruleUrl"]}',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f'{circle} <{legacy_alert_alerting["ruleUrl"]}|*[{alert_state}] {legacy_alert_alerting["ruleName"]}*>',
                    },
                },
                {
                    'type': 'section',
                    'text': {'type': 'mrkdwn', 'text': legacy_alert_alerting['message']},
                    **alert_values,
                },
                {
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
                                {'text': {'type': 'plain_text', 'text': 'wake'}, 'value': '0'},
                                {'text': {'type': 'plain_text', 'text': '15 min'}, 'value': '15'},
                                {'text': {'type': 'plain_text', 'text': '30 min'}, 'value': '30'},
                                {'text': {'type': 'plain_text', 'text': '1 hour'}, 'value': '60'},
                                {'text': {'type': 'plain_text', 'text': '2 hours'}, 'value': '120'},
                                {'text': {'type': 'plain_text', 'text': '5 hours'}, 'value': '300'},
                                {'text': {'type': 'plain_text', 'text': '1 day'}, 'value': '1440'},
                            ],
                        }
                    ],
                },
            ],
        }

    async def test_ok_alert_received__message_published(
        self,
        client: AiohttpClient,
        slack_client,
        legacy_alert_ok,
        webhook_url,
        channel,
    ):
        # act
        resp = await client.post(webhook_url, json=legacy_alert_ok)

        # assert
        assert resp.status == 200
        assert await resp.text() == ''
        assert slack_client.chat_postMessage.call_count == 1
        assert slack_client.chat_postMessage.call_args[1] == {
            'channel': f'#{channel}',
            'text': f'[OK] {legacy_alert_ok["ruleName"]}',
            'blocks': [
                {
                    'type': 'section',
                    'block_id': f'title|{legacy_alert_ok["ruleUrl"]}',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f':large_green_circle: <{legacy_alert_ok["ruleUrl"]}|*[OK] {legacy_alert_ok["ruleName"]}*>',
                    },
                }
            ],
        }

    async def test_snoozed_alert_received__alert_skipped(
        self, client, alert_filter, webhook_url, alert_metadata, legacy_alert_alerting, slack_client
    ):
        # arrange
        await alert_filter.snooze(
            channel_name=alert_metadata.channel_name,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by='user_nick',
            minutes=10,
        )

        # act
        resp = await client.post(webhook_url, json=legacy_alert_alerting)

        # assert
        assert resp.status == 200
        assert await resp.text() == ''
        assert slack_client.chat_postMessage.call_count == 0

    async def test_request_with_authorization__credentials_is_correct(
        self, config, client, webhook_url, legacy_alert_alerting
    ):
        # arrange
        credentials = ('admin', 'admin')
        config.accounts_ = dict([credentials])

        # act
        resp = await client.post(
            webhook_url,
            json=legacy_alert_alerting,
            auth=BasicAuth(*credentials),
        )

        # assert
        assert resp.status == 200

    async def test_request_with_authorization__credentials_is_not_correct(
        self, client, config, webhook_url, legacy_alert_alerting
    ):
        # arrange
        config.accounts_.update({'admin': 'admin'})

        # act
        resp = await client.post(
            webhook_url,
            json=legacy_alert_alerting,
            auth=BasicAuth('admin', 'bad_password'),
        )

        # assert
        assert resp.status == 401
        assert await resp.text() == 'Authorisation failed'


async def test_grafana_alert_view(
    client: AiohttpClient, slack_client, legacy_alert_alerting, webhook_url, channel
):
    # act
    resp = await client.get('/health-check/')

    # assert
    assert resp.status == 200
    assert await resp.json() == {'status': 'ok'}
