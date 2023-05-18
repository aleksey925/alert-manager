from aiohttp import web
from aiohttp_deps import Depends, Form, Json, Query, Router

from alert_manager.config import get_config
from alert_manager.services.alert_filter import BaseAlertFilter
from alert_manager.services.auth import verify_request_signature
from alert_manager.services.slack.message import (
    build_alert_message,
    get_rule_url_from_title,
    post_alert,
)
from alert_manager.web.entities.grafana import GrafanaAlertRequest
from alert_manager.web.entities.slack import SlackInteractiveActionForm

router = Router()
config = get_config()


@router.post('/webhook/grafana/')
async def grafana_alert_handler(
    channel: str = Depends(Query()),
    payload: GrafanaAlertRequest = Depends(Json()),
    request: web.Request = Depends(),
) -> web.Response:
    """
    Accepts and processes alerts from grafana.
    """
    alert_filter: BaseAlertFilter = request.app['alert_filter']
    if await alert_filter.is_snoozed(payload.rule_url):
        return web.Response()

    text, blocks = build_alert_message(payload)
    await post_alert(client=request.app['slack_client'], text=text, blocks=blocks, channel=channel)
    return web.Response()


@router.post('/slack/interactive/')
async def handle_slack_interactive(
    form: SlackInteractiveActionForm = Depends(Form()),
    request: web.Request = Depends(),
    _: None = Depends(verify_request_signature),
) -> web.Response:
    """
    Handles actions from the chat (for example pressing buttons, etc.)

    Features -> Interactivity & Shortcuts -> Interactivity
    https://api.slack.com/apps/<bot_id>/interactive-messages
    """
    payload = form.payload
    alert_filter: BaseAlertFilter = request.app['alert_filter']

    rule_url = get_rule_url_from_title(payload.message.blocks[0]['text']['text'])
    if not rule_url:
        return web.json_response({'msg': 'Failed to extract rule_url from message'}, status=400)

    minutes = payload.actions[0]['selected_option']['value']
    if minutes == 'wake':
        await alert_filter.wake(rule_url)
    else:
        await alert_filter.snooze(rule_url, int(minutes))
    return web.json_response()
