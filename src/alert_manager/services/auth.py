import typing as t

from aiohttp import web
from aiohttp_deps import Depends
from slack_sdk.signature import SignatureVerifier

from alert_manager.exceptions import UnauthorizedRequestError


async def verify_request_signature(request: web.Request = Depends()) -> None:
    slack_signature_verifier: SignatureVerifier = request.app['slack_signature_verifier']
    is_valid = slack_signature_verifier.is_valid_request(
        await request.text(), t.cast(dict[str, str], request.headers)
    )
    if not is_valid:
        raise UnauthorizedRequestError('Failed to authenticate request')
