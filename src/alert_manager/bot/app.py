from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.web.async_client import AsyncWebClient

from alert_manager.bot.handlers import Dispatcher
from alert_manager.services.alert_filter_backend import BaseAlertFilter


async def create_client(
    slack_client: AsyncWebClient,
    slack_socket_mode_token: str,
    alert_filter: BaseAlertFilter,
    use_channel_id: bool,
) -> SocketModeClient:
    slack_socket_client = SocketModeClient(
        app_token=slack_socket_mode_token,
        web_client=slack_client,
    )

    dispatcher = Dispatcher(slack_client, alert_filter, use_channel_id=use_channel_id)
    slack_socket_client.socket_mode_request_listeners.append(dispatcher)  # type: ignore[arg-type]
    await slack_socket_client.connect()  # type: ignore[no-untyped-call]
    return slack_socket_client
