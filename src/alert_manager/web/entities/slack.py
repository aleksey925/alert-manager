import json
import typing as t

from pydantic import BaseModel


class SlackMessage(BaseModel):
    text: str
    blocks: list[dict[str, t.Any]]


class SlackInteractiveActionPayload(BaseModel):
    type: str
    message: SlackMessage
    state: dict[str, t.Any]
    actions: list[dict[str, t.Any]]
    response_url: str


class SlackInteractiveActionForm(BaseModel):
    payload: SlackInteractiveActionPayload

    def __init__(self, **kwargs: t.Any) -> None:
        if 'payload' in kwargs:
            kwargs['payload'] = json.loads(kwargs['payload'])

        super().__init__(**kwargs)
