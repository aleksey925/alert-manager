from enum import Enum


class GrafanaAlertState(Enum):
    ok = 'ok'
    paused = 'paused'
    no_data = 'no_data'
    pending = 'pending'
    alerting = 'alerting'
