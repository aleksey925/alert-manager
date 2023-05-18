import typing as t

from aiohttp import web

from alert_manager.exceptions import UnauthorizedRequestError


@web.middleware
async def global_error_handler(
    request: web.Request, handler: t.Callable[[web.Request], t.Awaitable[web.StreamResponse]]
) -> web.StreamResponse:
    try:
        return await handler(request)
    except UnauthorizedRequestError as exc:
        return web.json_response({'msg': str(exc)}, status=401)
