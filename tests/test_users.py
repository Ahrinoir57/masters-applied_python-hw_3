import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import link_app.users
from pytest_mock import MockerFixture
import jwt
import pytest
import datetime
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


@pytest.mark.asyncio
async def test_create_login_user(mocker: MockerFixture):
    register_patch = mocker.patch('link_app.db.register_user_to_db')

    login='abcd'
    password='1234'

    encoded_token, err = await link_app.users.register_user(login, password)

    assert err is None

    login_patch = mocker.patch('link_app.db.get_user_by_login_password_db', return_value=57)

    encoded_token = await link_app.users.login_user(login, password)
    login_patch.assert_called_once_with(login, password)
    assert jwt.decode(encoded_token, link_app.users.salt, algorithms=["HS256"])['login'] == login


@pytest.mark.asyncio
async def test_login_non_existent_user(mocker: MockerFixture):
    login_patch = mocker.patch('link_app.db.get_user_by_login_password_db', return_value=None)

    login='abcd'
    password='1234'

    encoded_token = await link_app.users.login_user(login, password)
    login_patch.assert_called_once_with(login, password)
    assert encoded_token is None


@pytest.mark.asyncio
async def test_current_user(mocker: MockerFixture):
    register_patch = mocker.patch('link_app.db.register_user_to_db')

    login='abcd'
    password='1234'

    encoded_token, err = await link_app.users.register_user(login, password)

    current_user_patch = mocker.patch('link_app.db.get_user_by_login_db', return_value=1)

    user_id, err = await link_app.users.current_user(encoded_token)

    assert user_id == 1
    assert err is None
    current_user_patch.assert_called_once_with(login)


@pytest.mark.asyncio
async def test_current_user_invalid_token(mocker: MockerFixture):
    current_user_patch = mocker.patch('link_app.db.get_user_by_login_db', return_value=None)

    user_id, err = await link_app.users.current_user('invalid_token')

    assert user_id == None
    assert err == 'Invalid token'
    current_user_patch.assert_not_called()


@pytest.mark.asyncio
async def test_current_user_expired_token(mocker: MockerFixture):
    expires_at = str(datetime.datetime.now() - datetime.timedelta(hours=1))

    token = jwt.encode({"login": 'abcd', 'expires_at': expires_at}, link_app.users.salt, algorithm="HS256")

    current_user_patch = mocker.patch('link_app.db.get_user_by_login_db', return_value=None)

    user_id, err = await link_app.users.current_user(token)

    assert user_id == None
    assert err == 'Expired token'
    current_user_patch.assert_not_called()


@pytest.mark.asyncio
async def test_current_user_invalid_login(mocker: MockerFixture):
    expires_at = str(datetime.datetime.now() + datetime.timedelta(hours=1))

    token = jwt.encode({"login": 'abcd', 'expires_at': expires_at}, link_app.users.salt, algorithm="HS256")

    current_user_patch = mocker.patch('link_app.db.get_user_by_login_db', return_value=None)

    user_id, err = await link_app.users.current_user(token)

    assert user_id == None
    assert err == 'Invalid login'
    current_user_patch.assert_called_once_with('abcd')