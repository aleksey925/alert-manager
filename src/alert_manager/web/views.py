from aiohttp import web
from aiohttp_deps import Depends, Json, Query, Router

from alert_manager.config import get_config
from alert_manager.services.alert_filter_backend import BaseAlertFilter
from alert_manager.services.slack.message import (
    build_alert_message,
    post_alert,
)
from alert_manager.web.entities.grafana import GrafanaAlertRequest

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
