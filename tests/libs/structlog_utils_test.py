import pytest
from pytest_mock import MockFixture

from alert_manager.libs.structlog_utils import TimeStamper


@pytest.mark.parametrize('fmt', ['unix', None])
def test_time_stamper__default_stamper(mocker: MockFixture, fmt):
    # arrange
    timestamp = 1234567890.123456
    mocker.patch('time.time', return_value=1234567890.123456)

    # act
    result = TimeStamper(fmt=fmt)._stamper({'event': 'test'})

    # assert
    assert result['timestamp'] == timestamp


def test_time_stamper__unix_ms_stamper(mocker: MockFixture):
    # arrange
    timestamp = 1234567890.123456
    mocker.patch('time.time', return_value=1234567890.123456)

    # act
    result = TimeStamper(fmt='unix_ms')._stamper({'event': 'test'})

    # assert
    assert result['timestamp'] == timestamp * 1000


def test_time_stamper__custom_key_stamper(mocker: MockFixture):
    # arrange
    timestamp = 1234567890.123456
    mocker.patch('time.time', return_value=1234567890.123456)

    # act
    result = TimeStamper(key='custom_key')._stamper({'event': 'test'})

    # assert
    assert result['custom_key'] == timestamp
