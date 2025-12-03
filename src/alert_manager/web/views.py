from aiohttp import web
from aiohttp_deps import Depends, Json, Query, Router

from alert_manager.libs.security import require_user
from alert_manager.services.alert_filter_backend import BaseAlertFilter
from alert_manager.services.slack.message import MessageBuilder
from alert_manager.web.entities.grafana import GrafanaAlertRequest

router = Router()


@router.post('/webhook/grafana/')
async def grafana_alert_view(
    channel_id: str | None = Depends(Query(default=None)),
    channel_name: str | None = Depends(Query(default=None, alias='channel')),
    payload: GrafanaAlertRequest = Depends(Json()),
    request: web.Request = Depends(),
    _: str | None = Depends(require_user),
) -> web.Response:
    """
    Accepts and processes alerts from grafana.
    """
    use_channel_id: bool = request.app['use_channel_id']
    alert_filter: BaseAlertFilter = request.app['alert_filter']

    if use_channel_id:
        if not channel_id:
            return web.Response(
                status=400,
                text='channel_id query parameter is required when USE_CHANNEL_ID=true',
            )
        filter_channel = channel_id
        slack_channel = channel_id
    else:
        if not channel_name:
            return web.Response(
                status=400,
                text='channel query parameter is required when USE_CHANNEL_ID=false',
            )
        filter_channel = channel_name
        slack_channel = f'#{channel_name}'

    if await alert_filter.is_snoozed(filter_channel, payload.rule_url):
        return web.Response()

    text, blocks = MessageBuilder.create_alert_message(
        state=payload.state,
        title=payload.title,
        rule_url=payload.rule_url,
        message=payload.message,
        eval_matches=payload.eval_matches,
    )
    await request.app['slack_client'].chat_postMessage(
        channel=slack_channel,
        text=text,
        blocks=blocks,
    )
    return web.Response()


@router.get('/health-check/')
async def health_check_view() -> web.Response:
    return web.json_response({'status': 'ok'})
