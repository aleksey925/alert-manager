from aiohttp import BasicAuth, hdrs, web
from taskiq_dependencies import Depends


def require_user(
    accounts: dict[str, str] | None = None, request: web.Request = Depends()
) -> str | None:
    if accounts is None:
        return None

    auth_header = request.headers.get(hdrs.AUTHORIZATION)
    if not auth_header:
        raise web.HTTPUnauthorized(text='No authorization header')

    try:
        basic_auth = BasicAuth.decode(auth_header=auth_header)
    except ValueError as err:
        raise web.HTTPUnauthorized(text=str(err))

    saved_password = accounts.get(basic_auth.login)
    if saved_password is None:
        raise web.HTTPUnauthorized(text='Authorisation failed')

    if basic_auth.password != saved_password:
        raise web.HTTPUnauthorized(text='Authorisation failed')

    return basic_auth.login
