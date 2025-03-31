import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import link_app.sqlite_db
from pytest_mock import MockerFixture
import pytest
import datetime
import pytest_asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest_asyncio.fixture
async def sqlite_service():
    """Ensure that HTTP service is up and responsive."""

    try:
        await link_app.sqlite_db.create_sql_database()
        yield 
    
    finally:
        os.remove("./database/test.db")
        os.rmdir("./database/")


@pytest.mark.asyncio
async def test_find_link_url(sqlite_service):

    short_code = 'aaaa'
    url = 'yandex.ru'
    user_id = 1
    expires_at = '2025-31-01'

    await link_app.sqlite_db.add_link_to_db(short_code, url, user_id, expires_at)

    f_user_id, f_short_code, f_expires_at = await link_app.sqlite_db.find_link_by_url(url)
    assert f_user_id == user_id 
    assert f_short_code == short_code
    assert f_expires_at == expires_at 


@pytest.mark.asyncio
async def test_find_link_short_code(sqlite_service):

    short_code = 'aaaa'
    url = 'yandex.ru'
    user_id = 1
    expires_at = '2025-31-01'

    await link_app.sqlite_db.add_link_to_db(short_code, url, user_id, expires_at)

    _, f_url, f_user_id, f_expires_at = await link_app.sqlite_db.get_link_from_db(short_code)
    assert f_user_id == user_id 
    assert f_url == url
    assert f_expires_at == expires_at 


@pytest.mark.asyncio
async def test_find_link_short_code(sqlite_service):

    short_code = 'aaaa'
    url = 'yandex.ru'
    user_id = 1
    expires_at = '2025-31-01'

    await link_app.sqlite_db.add_link_to_db(short_code, url, user_id, expires_at)

    _, f_url, f_user_id, f_expires_at = await link_app.sqlite_db.get_link_from_db(short_code)
    assert f_user_id == user_id 
    assert f_url == url
    assert f_expires_at == expires_at 


@pytest.mark.asyncio
async def test_delete_link(sqlite_service):

    short_code = 'aaaa'
    url = 'yandex.ru'
    user_id = 1
    expires_at = '2025-31-01'

    await link_app.sqlite_db.add_link_to_db(short_code, url, user_id, expires_at)

    link_id, _, _, _ = await link_app.sqlite_db.get_link_from_db(short_code)

    await link_app.sqlite_db.delete_link_from_db(link_id)

    link_id, _, _, _ = await link_app.sqlite_db.get_link_from_db(short_code)

    assert link_id is None


@pytest.mark.asyncio
async def test_find_user(sqlite_service):

    login='abcd'
    password='1234'

    await link_app.sqlite_db.register_user_to_db(login, password)

    user_id = await link_app.sqlite_db.get_user_by_login_db(login)
    assert user_id is not None

    log_pas_user_id = await link_app.sqlite_db.get_user_by_login_password_db(login, password)
    assert user_id == log_pas_user_id



@pytest.mark.asyncio
async def test_active_codes(sqlite_service):

    short_code = 'aaaa'
    url = 'yandex.ru'
    user_id = 1
    expires_at = '2025-31-01'

    await link_app.sqlite_db.add_link_to_db(short_code, url, user_id, expires_at)

    await link_app.sqlite_db.add_link_to_db('aaab', url, user_id, expires_at)

    await link_app.sqlite_db.add_link_to_db('aaac', url, user_id, expires_at)


    codes = await link_app.sqlite_db.get_active_codes()
    assert codes == ['aaaa', 'aaab', 'aaac']


@pytest.mark.asyncio
async def test_get_stats(sqlite_service):

    short_code = 'aaaa'
    url = 'yandex.ru'
    user_id = 1
    expires_at = '2025-31-01'

    await link_app.sqlite_db.add_link_to_db(short_code, url, user_id, expires_at)

    link_id, _, _, _ = await link_app.sqlite_db.get_link_from_db(short_code)

    await link_app.sqlite_db.log_request_to_db(link_id, user_id)
    await link_app.sqlite_db.log_request_to_db(link_id, user_id + 1)
    await link_app.sqlite_db.log_request_to_db(link_id, user_id)

    request_count, latest_request, created_at = await link_app.sqlite_db.get_stats_from_db(link_id)

    assert request_count == 3
    assert latest_request is not None
    assert created_at is not None