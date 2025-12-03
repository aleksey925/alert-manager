from pydantic import BaseModel


class AlertMetadata(BaseModel):
    title: str
    rule_url: str
    snoozed_by: str
    snoozed_until: int | float
    channel: str
