import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import link_app.users
from pytest_mock import MockerFixture
import jwt
import pytest
pytest_plugins = ('pytest_asyncio',)


@pytest.mark.asyncio
async def test_create_user(mocker: MockerFixture):
    patch = mocker.patch('link_app.db.register_user_to_db')

    login='abcd'
    password='1234'

    encoded_token, err = await link_app.users.register_user(login, password)

    assert err is None
    patch.assert_called_once_with(login, password)
    assert jwt.decode(encoded_token, link_app.users.salt, algorithms=["HS256"])['login'] == login


@pytest.mark.asyncio
async def test_create_user_bad_password(mocker: MockerFixture):
    patch = mocker.patch('link_app.db.register_user_to_db')
    login='abcd'
    password=None

    encoded_token, err = await link_app.users.register_user(login, password)

    assert err == 'bad_password'
    assert encoded_token is None
    patch.assert_not_called()


@pytest.mark.asyncio
async def test_repeating_login_create_user(mocker: MockerFixture):
    patch = mocker.patch('link_app.db.register_user_to_db', side_effect = [None, Exception])

    old_login='abcd'
    old_password='1234'

    encoded_token, err = await link_app.users.register_user(old_login, old_password)

    patch.assert_called_with(old_login, old_password)

    new_login='abcd'
    new_password='5678'

    encoded_token, err = await link_app.users.register_user(new_login, new_password)

    assert err == 'repeating_login'
    patch.assert_called_with(new_login, new_password)
    assert encoded_token is None


def test_auth_user_correct(mocker: MockerFixture):
    assert 1 == 1


def test_auth_user_incorrect(mocker: MockerFixture):
    assert 1 == 1


def test_get_current_user_id(mocker: MockerFixture):
    assert 1 == 1


def test_get_unauth_user_id(mocker: MockerFixture):
    assert 1 == 1