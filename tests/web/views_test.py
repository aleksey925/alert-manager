from unittest.mock import MagicMock

import pytest
from aiohttp import web
from aiohttp.helpers import BasicAuth
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound
from pytest_aiohttp.plugin import AiohttpClient
from pytest_mock import MockFixture

from alert_manager.main import error_logging_middleware


class TestGrafanaAlertViewLegacyAlert:
    async def test_new_alert_received__message_published(
        self,
        client: AiohttpClient,
        slack_client,
        legacy_alert_alerting,
        webhook_url,
        channel,
        snooze_for_block,
    ):
        # arrange
        alert_payload = legacy_alert_alerting
        text = f'[Alerting] {alert_payload["ruleName"]}'

        # act
        resp = await client.post(webhook_url, json=alert_payload)

        # assert
        assert resp.status == 200
        assert await resp.text() == ''
        assert slack_client.chat_postMessage.call_count == 1
        assert slack_client.chat_postMessage.call_args[1] == {
            'channel': f'#{channel}',
            'text': text,
            'blocks': [
                {
                    'type': 'section',
                    'block_id': f'title|{alert_payload["ruleUrl"]}',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f':red_circle: <{alert_payload["ruleUrl"]}|*{text}*>',
                    },
                },
                {
                    'type': 'section',
                    'text': {'type': 'mrkdwn', 'text': alert_payload['message']},
                    'fields': [
                        {
                            'type': 'mrkdwn',
                            'text': (
                                f'*{alert_payload["evalMatches"][0]["metric"]}:* '
                                f'{alert_payload["evalMatches"][0]["value"]}'
                            ),
                        },
                        {
                            'type': 'mrkdwn',
                            'text': (
                                f'*{alert_payload["evalMatches"][1]["metric"]}:* '
                                f'{alert_payload["evalMatches"][1]["value"]}'
                            ),
                        },
                    ],
                },
                snooze_for_block,
            ],
        }

    async def test_no_data__message_published(
        self,
        client: AiohttpClient,
        slack_client,
        legacy_alert_no_data,
        webhook_url,
        channel,
        snooze_for_block,
    ):
        # arrange
        text = f'[No Data] {legacy_alert_no_data["ruleName"]}'

        # act
        resp = await client.post(webhook_url, json=legacy_alert_no_data)

        # assert
        assert resp.status == 200
        assert await resp.text() == ''
        assert slack_client.chat_postMessage.call_count == 1
        assert slack_client.chat_postMessage.call_args[1] == {
            'channel': f'#{channel}',
            'text': text,
            'blocks': [
                {
                    'type': 'section',
                    'block_id': f'title|{legacy_alert_no_data["ruleUrl"]}',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f':white_circle: <{legacy_alert_no_data["ruleUrl"]}|*{text}*>',
                    },
                },
                {'text': {'text': 'message', 'type': 'mrkdwn'}, 'type': 'section'},
                snooze_for_block,
            ],
        }

    async def test_no_data_alerting__message_published(
        self,
        client: AiohttpClient,
        slack_client,
        legacy_alert_no_data_alerting,
        webhook_url,
        channel,
        snooze_for_block,
    ):
        # arrange
        text = f'[Alerting] {legacy_alert_no_data_alerting["ruleName"]}'

        # act
        resp = await client.post(webhook_url, json=legacy_alert_no_data_alerting)

        # assert
        assert resp.status == 200
        assert await resp.text() == ''
        assert slack_client.chat_postMessage.call_count == 1
        assert slack_client.chat_postMessage.call_args[1] == {
            'channel': f'#{channel}',
            'text': text,
            'blocks': [
                {
                    'type': 'section',
                    'block_id': f'title|{legacy_alert_no_data_alerting["ruleUrl"]}',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f':red_circle: <{legacy_alert_no_data_alerting["ruleUrl"]}|*{text}*>',
                    },
                },
                snooze_for_block,
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
                        'text': (
                            f':large_green_circle: <{legacy_alert_ok["ruleUrl"]}|*[OK] {legacy_alert_ok["ruleName"]}*>'
                        ),
                    },
                }
            ],
        }

    async def test_snoozed_alert_received__alert_skipped(
        self,
        client,
        alert_filter,
        channel,
        alert_metadata,
        legacy_alert_alerting,
        slack_client,
    ):
        # arrange
        await alert_filter.snooze(
            channel=alert_metadata.channel,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            snoozed_by='user_nick',
            minutes=10,
        )
        webhook_url = f'/webhook/grafana/?channel={channel}'

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
        config.accounts = dict([credentials])

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
        config.accounts.update({'admin': 'admin'})

        # act
        resp = await client.post(
            webhook_url,
            json=legacy_alert_alerting,
            auth=BasicAuth('admin', 'bad_password'),
        )

        # assert
        assert resp.status == 401
        assert await resp.text() == 'Authorisation failed'

    @pytest.fixture(name='snooze_for_block')
    def snooze_for_block_fixture(self):
        return {
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
                        {'text': {'type': 'plain_text', 'text': '8 hours'}, 'value': '480'},
                        {'text': {'type': 'plain_text', 'text': '1 day'}, 'value': '1440'},
                        {'text': {'type': 'plain_text', 'text': '2 day'}, 'value': '2880'},
                    ],
                }
            ],
        }


async def test_grafana_alert_view(client: AiohttpClient, slack_client, webhook_url, channel):
    # act
    resp = await client.get('/health-check/')

    # assert
    assert resp.status == 200
    assert await resp.json() == {'status': 'ok'}


class TestErrorLoggingMiddleware:
    async def test_successful_response__no_logging(
        self,
        client: AiohttpClient,
        mock_capture_message: MagicMock,
        mock_logger: MagicMock,
    ):
        # act
        resp = await client.get('/success')

        # assert
        assert resp.status == 200
        mock_capture_message.assert_not_called()
        mock_logger.warning.assert_not_called()

    async def test_error_response__logs_error(
        self,
        client: AiohttpClient,
        mock_capture_message: MagicMock,
        mock_logger: MagicMock,
    ):
        # act
        resp = await client.get('/error-response')

        # assert
        assert resp.status == 400
        mock_capture_message.assert_called_once_with(
            message='HTTP error response',
            level='warning',
            extra={
                'method': 'GET',
                'path': '/error-response',
                'status': 400,
                'req_body': '',
                'resp_body': 'Bad request error',
            },
        )
        mock_logger.warning.assert_called_once_with(
            'HTTP error response',
            method='GET',
            path='/error-response',
            status=400,
            req_body='',
            resp_body='Bad request error',
        )

    async def test_http_exception_raised__logs_error(
        self,
        client: AiohttpClient,
        mock_capture_message: MagicMock,
        mock_logger: MagicMock,
    ):
        # act
        resp = await client.get('/raises-exception')

        # assert
        assert resp.status == 404
        mock_capture_message.assert_called_once_with(
            message='HTTP error response',
            level='warning',
            extra={
                'method': 'GET',
                'path': '/raises-exception',
                'status': 404,
                'req_body': '',
                'resp_body': '404: Not Found',
            },
        )
        mock_logger.warning.assert_called_once_with(
            'HTTP error response',
            method='GET',
            path='/raises-exception',
            status=404,
            req_body='',
            resp_body='404: Not Found',
        )

    async def test_http_exception_with_custom_text__logs_custom_text(
        self,
        client: AiohttpClient,
        mock_capture_message: MagicMock,
    ):
        # act
        resp = await client.get('/raises-bad-request')

        # assert
        assert resp.status == 400
        assert mock_capture_message.call_args[1]['extra']['resp_body'] == 'Custom error message'

    @pytest.fixture(name='mock_capture_message')
    def mock_capture_message_fixture(self, mocker: MockFixture) -> MagicMock:
        return mocker.patch('alert_manager.main.capture_message')

    @pytest.fixture(name='mock_logger')
    def mock_logger_fixture(self, mocker: MockFixture) -> MagicMock:
        return mocker.patch('alert_manager.main.logger')

    @pytest.fixture(name='app')
    def app_fixture(self, mock_capture_message: MagicMock, mock_logger: MagicMock):
        async def success_handler(request: web.Request) -> web.Response:
            return web.Response(text='OK')

        async def error_response_handler(request: web.Request) -> web.Response:
            return web.Response(status=400, text='Bad request error')

        async def raises_exception_handler(request: web.Request) -> web.Response:
            raise HTTPNotFound

        async def raises_bad_request_handler(request: web.Request) -> web.Response:
            raise HTTPBadRequest(text='Custom error message')

        app = web.Application(middlewares=[error_logging_middleware])
        app.router.add_get('/success', success_handler)
        app.router.add_get('/error-response', error_response_handler)
        app.router.add_get('/raises-exception', raises_exception_handler)
        app.router.add_get('/raises-bad-request', raises_bad_request_handler)
        return app

    @pytest.fixture
    async def client(self, aiohttp_client, app) -> AiohttpClient:
        return await aiohttp_client(app)
