import pytest
from aiohttp import hdrs, web
from aiohttp.helpers import BasicAuth
from pytest_mock import MockFixture

from alert_manager.libs.security import require_user


@pytest.mark.parametrize('accounts', [None, {}])
def test_require_user_no_accounts(accounts):
    # act
    login = require_user(accounts)

    # assert
    assert login is None


def test_require_user_correct_auth(mocker: MockFixture):
    # arrange
    request = mocker.MagicMock()
    request.headers = {hdrs.AUTHORIZATION: BasicAuth('testuser', 'password').encode()}
    accounts = {'testuser': 'password'}

    # act
    login = require_user(accounts, request)

    # assert
    assert login == 'testuser'


def test_require_user__wrong_password(mocker: MockFixture):
    # arrange
    request = mocker.MagicMock()
    request.headers = {hdrs.AUTHORIZATION: BasicAuth('testuser', 'wrongpassword').encode()}
    accounts = {'testuser': 'password'}

    # act
    with pytest.raises(web.HTTPUnauthorized) as exc_info:
        require_user(accounts, request)

    # assert
    assert 'Authorisation failed' == str(exc_info.value.text)


def test_require_user__no_user(mocker: MockFixture):
    # arrange
    request = mocker.MagicMock()
    request.headers = {hdrs.AUTHORIZATION: BasicAuth('wronguser', 'password').encode()}
    accounts = {'testuser': 'password'}

    # act
    with pytest.raises(web.HTTPUnauthorized) as exc_info:
        require_user(accounts, request)

    # assert
    assert 'Authorisation failed' in str(exc_info.value.text)


def test_require_user__no_auth_header(mocker: MockFixture):
    # arrange
    request = mocker.MagicMock()
    request.headers = {}
    accounts = {'testuser': 'password'}

    # act
    with pytest.raises(web.HTTPUnauthorized) as exc_info:
        require_user(accounts, request)

    # assert
    assert 'No authorization header' in str(exc_info.value.text)


def test_require_user__invalid_auth_header(mocker: MockFixture):
    # arrange
    request = mocker.MagicMock()
    request.headers = {hdrs.AUTHORIZATION: 'invalid'}
    accounts = {'testuser': 'password'}

    # act
    with pytest.raises(web.HTTPUnauthorized) as exc_info:
        require_user(accounts, request)

    # assert
    assert 'Could not parse authorization header.' == str(exc_info.value.text)
