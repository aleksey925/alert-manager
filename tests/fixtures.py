import json
from pathlib import Path

import pytest

__all__ = [
    'legacy_alert_alerting',
    'legacy_alert_no_data',
    'legacy_alert_no_data_alerting',
    'legacy_alert_ok',
]


@pytest.fixture
def legacy_alert_alerting(test_dir: Path):
    return json.loads((test_dir / 'data' / 'legacy_alerts.json').read_text())['alerting']


@pytest.fixture
def legacy_alert_no_data(test_dir: Path):
    return json.loads((test_dir / 'data' / 'legacy_alerts.json').read_text())['no_data']


@pytest.fixture
def legacy_alert_no_data_alerting(test_dir: Path):
    return json.loads((test_dir / 'data' / 'legacy_alerts.json').read_text())['no_data_alerting']


@pytest.fixture
def legacy_alert_ok(test_dir: Path):
    return json.loads((test_dir / 'data' / 'legacy_alerts.json').read_text())['ok']
