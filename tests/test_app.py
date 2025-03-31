import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import link_app.app
from pytest_mock import MockerFixture
import pytest
import datetime
import requests
import jwt
pytest_plugins = ('pytest_asyncio')

from fastapi.testclient import TestClient

app = link_app.app.app

client = TestClient(app)


def test_register_user(mocker: MockerFixture):
    patch = mocker.patch('link_app.users.register_user', return_value=('haha', None))
    redis_patch = mocker.patch('link_app.redis.cache_token')

    login='abcd'
    password='1234'

    response = client.post("/auth/register", json={'login': login, 'password': password})

    assert response.status_code == 200
    patch.assert_called_once_with(login, password)
    redis_patch.assert_called_once_with(login, password, 'haha')
    assert response.json()['token'] is not None


def test_login_user_cached_token(mocker: MockerFixture):
    patch = mocker.patch('link_app.users.login_user', return_value='haha')
    redis_patch = mocker.patch('link_app.redis.cache_token')
    redis_get_patch = mocker.patch('link_app.redis.get_token', return_value='haha')

    login="abcd"
    password="1234"

    response = client.post("/auth/login", json={"login": login, "password": password})

    assert response.status_code == 200
    redis_get_patch.assert_called_once_with(login, password)
    assert response.json()['token'] is not None


def test_login_user_no_cache(mocker: MockerFixture):
    patch = mocker.patch('link_app.users.login_user', return_value='haha')
    redis_patch = mocker.patch('link_app.redis.cache_token')
    redis_get_patch = mocker.patch('link_app.redis.get_token', return_value=None)

    login="abcd"
    password="1234"

    response = client.post("/auth/login", json={"login": login, "password": password})

    assert response.status_code == 200
    patch.assert_called_once_with(login, password)
    redis_patch.assert_called_once_with(login, password, 'haha')
    redis_get_patch.assert_called_once_with(login, password)
    assert response.json()['token'] is not None



def test_create_link(mocker: MockerFixture):
    patch = mocker.patch('link_app.db.get_active_codes', return_value=['aaaa', 'aaab'])
    link_patch = mocker.patch('link_app.db.get_link_from_db', return_value=(None, None, None, None))
    adding_link_patch = mocker.patch('link_app.db.add_link_to_db')

    url = "yandex.ru"

    response = client.post(f"/links/shorten?url={url}")

    assert response.status_code == 200
    patch.assert_called_once_with()
    assert response.json()['short_code'] is not None


def test_create_link_duplicate_short_codes(mocker: MockerFixture):
    patch = mocker.patch('link_app.db.get_active_codes', return_value=['aaaa'])
    link_patch = mocker.patch('link_app.db.get_link_from_db', return_value=(1, None, None, None))
    adding_link_patch = mocker.patch('link_app.db.add_link_to_db')

    url = "yandex.ru"

    response = client.post(f"/links/shorten?url={url}&custom_alias=aaaa")

    assert response.status_code == 400


def test_delete_link(mocker: MockerFixture):
    patch = mocker.patch('link_app.users.current_user', return_value=(1, None))
    link_patch = mocker.patch('link_app.db.get_link_from_db', return_value=(1, None, 1, datetime.datetime.now() + datetime.timedelta(days=3)))
    del_link_patch = mocker.patch('link_app.db.delete_link_from_db')

    url = "yandex.ru"

    response = client.delete(f"/links/aaaa", headers={"Authorization": f"Bearer token"})

    assert response.status_code == 200


def test_delete_link_no_cred(mocker: MockerFixture):
    patch = mocker.patch('link_app.users.current_user', return_value=(1, None))
    link_patch = mocker.patch('link_app.db.get_link_from_db', return_value=(1, None, 1, datetime.datetime.now() + datetime.timedelta(days=3)))
    del_link_patch = mocker.patch('link_app.db.delete_link_from_db')

    url = "yandex.ru"

    response = client.delete(f"/links/aaaa")

    assert response.status_code == 403


def test_update_link(mocker: MockerFixture):
    patch = mocker.patch('link_app.users.current_user', return_value=(1, None))
    link_patch = mocker.patch('link_app.db.get_link_from_db', return_value=(1, None, 1, datetime.datetime.now() + datetime.timedelta(days=3)))
    del_link_patch = mocker.patch('link_app.db.delete_link_from_db')
    add_link_patch = mocker.patch('link_app.db.add_link_to_db')

    url = "yandex.ru"

    response = client.put(f"/links/aaaa", headers={"Authorization": f"Bearer token"}, json={'url': url})

    assert response.status_code == 200


def test_update_link_no_cred(mocker: MockerFixture):
    patch = mocker.patch('link_app.users.current_user', return_value=(1, None))
    link_patch = mocker.patch('link_app.db.get_link_from_db', return_value=(1, None, 1, datetime.datetime.now() + datetime.timedelta(days=3)))
    del_link_patch = mocker.patch('link_app.db.delete_link_from_db')

    url = "yandex.ru"

    response = client.put(f"/links/aaaa", json={'url': url})

    assert response.status_code == 403


def test_search_link(mocker: MockerFixture):
    patch = mocker.patch('link_app.db.find_link_by_url', return_value=(1, 'aaaa', datetime.datetime.now() + datetime.timedelta(days=3)))

    url = 'yandex.ru'

    response = client.get(f"/search?original_url={url}")

    assert response.json()['short_code'] == 'aaaa'
    patch.assert_called_once_with(url)
    assert response.status_code == 200


def test_search_link_no_short_code(mocker: MockerFixture):
    patch = mocker.patch('link_app.db.find_link_by_url', return_value=(1, None, datetime.datetime.now() + datetime.timedelta(days=3)))

    url = 'yandex.ru'

    response = client.get(f"/search?original_url={url}")

    assert response.status_code == 404
    patch.assert_called_once_with(url)


def test_search_link_expired_short_code(mocker: MockerFixture):
    patch = mocker.patch('link_app.db.find_link_by_url', return_value=(1, 'aaaa', datetime.datetime.now() - datetime.timedelta(days=3)))

    url = 'yandex.ru'

    response = client.get(f"/search?original_url={url}")

    assert response.status_code == 404
    patch.assert_called_once_with(url)


def test_short_code_stats_no_link(mocker: MockerFixture):
    patch = mocker.patch('link_app.db.get_link_from_db', return_value=(None, None, None, None))

    short_code = 'aaaa'

    response = client.get(f"/links/{short_code}/stats")

    assert response.status_code == 404
    patch.assert_called_once_with(short_code)


def test_short_code_stats(mocker: MockerFixture):
    patch = mocker.patch('link_app.db.get_link_from_db', return_value=(1111, None, None, None))
    stats_patch = mocker.patch('link_app.db.get_stats_from_db', return_value=(1, 2, 3))

    short_code = 'aaaa'

    response = client.get(f"/links/{short_code}/stats")

    assert response.status_code == 200
    patch.assert_called_once_with(short_code)
    stats_patch.assert_called_once_with(1111)
    assert response.json() == {'request_count': 1, 'last_request': 2, 'created_at': 3}


def test_user_stats(mocker: MockerFixture):
    patch = mocker.patch('link_app.users.current_user', return_value=(1, None))
    stats_patch = mocker.patch('link_app.db.get_all_user_links', return_value=['data'])

    response = client.get(f"/user/stats", headers={"Authorization": f"Bearer token"})

    assert response.status_code == 200
    patch.assert_called_once_with('token')
    stats_patch.assert_called_once_with(1)
    assert response.json() == ['data']


def test_use_link(mocker: MockerFixture):
    patch = mocker.patch('link_app.db.get_link_from_db', return_value=(1111, 'yandex.ru', 1, datetime.datetime.now() + datetime.timedelta(days=2)))
    exlend_life_patch =  mocker.patch('link_app.db.extend_link_life_db')
    request_patch =  mocker.patch('link_app.db.log_request_to_db')

    short_code = 'aaaa'
    response = client.get(f"/links/{short_code}", follow_redirects=False)

    assert response.status_code == 307
    patch.assert_called_once_with(short_code)



def test_use_link_no_link(mocker: MockerFixture):
    patch = mocker.patch('link_app.db.get_link_from_db', return_value=(None, None, None, None))

    short_code = 'aaaa'
    response = client.get(f"/links/{short_code}")

    assert response.status_code == 404
    patch.assert_called_once_with(short_code)


def test_use_expired_link(mocker: MockerFixture):
    patch = mocker.patch('link_app.db.get_link_from_db', return_value=(1111, 'yandex.ru', 1, datetime.datetime.now() - datetime.timedelta(days=3)))

    short_code = 'aaaa'
    response = client.get(f"/links/{short_code}")

    assert response.status_code == 404
    patch.assert_called_once_with(short_code)