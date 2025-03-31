import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import link_app.db
from pytest_mock import MockerFixture
import psycopg
import pytest
import datetime

pytest_plugins = ('pytest_asyncio',)

@pytest.fixture
def test_db():
    TEST_DB_URL = 'postgresql://postgres:some_password@localhost/testing'
    TEST_DB_NAME = 'testing'
    # autocommit=True start no transaction because CREATE/DROP DATABASE
    # cannot be executed in a transaction block.
    with psycopg.connect(TEST_DB_URL, autocommit=True) as conn:
        cur = conn.cursor()

        # create test DB, drop before
        cur.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}" WITH (FORCE)')
        cur.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')

        # Return (a new) connection to just created test DB
        # Unfortunately, you cannot directly change the database for an existing Psycopg connection. Once a connection is established to a specific database, it's tied to that database.
        with psycopg.connect(TEST_DB_URL, dbname=TEST_DB_NAME) as conn:
            yield conn

        cur.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}" WITH (FORCE)')


# @pytest.mark.asyncio
# async def test_find_link_url(postgresql):
#     test_conn_string = 'postgresql://postgres:some_password@localhost/postgres'
#     await link_app.db.create_sql_database(test_conn_string)

#     short_code = 'aaaa'
#     url = 'yandex.ru'
#     user_id = 1
#     expires_at = '2025-31-01'

#     await link_app.db.add_link_to_db(short_code, url, user_id, expires_at)

#     f_user_id, f_short_code, f_expires_at = await link_app.db.find_link_by_url(url)
#     assert f_user_id == user_id 
#     assert f_short_code == short_code
#     assert f_expires_at == expires_at 


