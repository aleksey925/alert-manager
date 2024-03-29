from pydantic import BaseModel, Field

from alert_manager.enums.grafana import GrafanaAlertState


class EvalMatch(BaseModel):
    metric: str
    value: int | float
    tags: dict[str, str] | None = Field(default=None)


class GrafanaAlertRequest(BaseModel):
    title: str
    message: str | None = Field(default=None)
    state: GrafanaAlertState
    rule_name: str = Field(alias='ruleName')
    rule_url: str = Field(alias='ruleUrl')
    eval_matches: list[EvalMatch] = Field(alias='evalMatches')
