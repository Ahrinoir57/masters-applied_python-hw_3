import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import link_app.db
from pytest_mock import MockerFixture
import pytest
import datetime
import requests
import time
pytest_plugins = ('pytest_asyncio')


@pytest.fixture(scope="session")
def postgres_service(docker_ip, docker_services):
    """Ensure that HTTP service is up and responsive."""

    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("postgresql", 5432)
    time.sleep(30)
    return f'postgresql://postgres:some_password@{docker_ip}:{port}/postgres'


@pytest.mark.asyncio
@pytest.mark.long
async def test_find_link_url(postgres_service):
    await link_app.db.create_sql_database(postgres_service)

    short_code = 'aaaa'
    url = 'yandex.ru'
    user_id = 1
    expires_at = datetime.datetime.now() + datetime.timedelta(days=3)

    await link_app.db.add_link_to_db(short_code, url, user_id, expires_at)

    f_user_id, f_short_code, f_expires_at = await link_app.db.find_link_by_url(url)
    assert f_user_id == user_id 
    assert f_short_code == short_code
    assert f_expires_at == expires_at 

    await link_app.db.db.execute("""DELETE FROM Links WHERE 1 = 1""")



@pytest.mark.asyncio
@pytest.mark.long
async def test_delete_link(postgres_service):
    await link_app.db.create_sql_database(postgres_service)

    short_code = 'aaaa'
    url = 'yandex.ru'
    user_id = 1
    expires_at = datetime.datetime.now() + datetime.timedelta(days=3)

    await link_app.db.add_link_to_db(short_code, url, user_id, expires_at)

    f_link_id, _, _, _= await link_app.db.get_link_from_db(short_code)

    await link_app.db.delete_link_from_db(f_link_id)

    link_id, _, _, _ = await link_app.db.get_link_from_db(short_code)

    assert link_id is None

    await link_app.db.db.execute("""DELETE FROM Links WHERE 1 = 1""")


@pytest.mark.asyncio
@pytest.mark.long
async def test_get_url_stats(postgres_service):
    await link_app.db.create_sql_database(postgres_service)

    short_code = 'aaaa'
    url = 'yandex.ru'
    user_id = 1
    expires_at = datetime.datetime.now() + datetime.timedelta(days=3)

    await link_app.db.add_link_to_db(short_code, url, user_id, expires_at)

    link_id, _, _, _= await link_app.db.get_link_from_db(short_code)

    await link_app.db.log_request_to_db(link_id, 1)
    await link_app.db.log_request_to_db(link_id, 2)
    await link_app.db.log_request_to_db(link_id, 3)

    request_count, _, _ = await link_app.db.get_stats_from_db(link_id)

    assert request_count == 3

    await link_app.db.db.execute("""DELETE FROM Requests WHERE 1 = 1""")
    await link_app.db.db.execute("""DELETE FROM Links WHERE 1 = 1""")


@pytest.mark.asyncio
@pytest.mark.long
async def test_get_active_codes(postgres_service):
    await link_app.db.create_sql_database(postgres_service)

    url = 'yandex.ru'
    user_id = 1
    expires_at = datetime.datetime.now() + datetime.timedelta(days=3)

    await link_app.db.add_link_to_db('aaaa', url, user_id, expires_at)
    await link_app.db.add_link_to_db('bbbb', url, user_id, expires_at)
    await link_app.db.add_link_to_db('cccc', url, user_id, expires_at)

    codes = await link_app.db.get_active_codes()
    assert codes == ['aaaa', 'bbbb', 'cccc']

    await link_app.db.db.execute("""DELETE FROM Links WHERE 1 = 1""")



@pytest.mark.asyncio
@pytest.mark.long
async def test_get_all_user_links(postgres_service):
    await link_app.db.create_sql_database(postgres_service)

    url = 'yandex.ru'
    user_id = 1
    expires_at = datetime.datetime.now() + datetime.timedelta(days=3)

    await link_app.db.add_link_to_db('aaaa', url, user_id, expires_at)
    await link_app.db.add_link_to_db('bbbb', url, user_id, expires_at)
    await link_app.db.add_link_to_db('cccc', url, user_id, expires_at)

    data = await link_app.db.get_all_user_links(user_id)
    assert len(data) == 3
    
    await link_app.db.db.execute("""DELETE FROM Links WHERE 1 = 1""")



@pytest.mark.asyncio
@pytest.mark.long
async def test_register_user(postgres_service):
    await link_app.db.create_sql_database(postgres_service)

    login = 'aaaa'
    password = '1234'

    await link_app.db.register_user_to_db(login, password)

    user_id = await link_app.db.get_user_by_login_db(login)
    assert user_id is not None

    user_id_2 = await link_app.db.get_user_by_login_password_db(login, password)

    assert user_id == user_id_2
    
    await link_app.db.db.execute("""DELETE FROM Users WHERE 1 = 1""")



