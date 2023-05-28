import logging

from aiohttp import web
from aiohttp_deps import Depends, Json, Query, Router

from alert_manager.config import get_config
from alert_manager.services.alert_filter_backend import BaseAlertFilter
from alert_manager.services.slack.message import MessageBuilder
from alert_manager.web.entities.grafana import GrafanaAlertRequest

logger = logging.getLogger(__name__)
router = Router()
config = get_config()


@router.post('/webhook/grafana/')
async def grafana_alert_view(
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

    text, blocks = MessageBuilder.create_alert_message(
        state=payload.state,
        title=payload.title,
        rule_url=payload.rule_url,
        message=payload.message,
        eval_matches=payload.eval_matches,
    )
    await request.app['slack_client'].chat_postMessage(
        channel=f'#{channel}',
        text=text,
        blocks=blocks,
    )
    return web.Response()


@router.get('/health-check/')
async def health_check_view() -> web.Response:
    return web.json_response({'status': 'ok'})
