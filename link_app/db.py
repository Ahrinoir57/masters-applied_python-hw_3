import os
import datetime
import asyncpg

create_table_statements = [ 
    """CREATE TABLE IF NOT EXISTS Links (
            link_id SERIAL PRIMARY KEY, 
            short_code TEXT NOT NULL, 
            url TEXT NOT NULL,
            user_id INT,
            created_at TIMESTAMP,
            expires_at TIMESTAMP, 
            active INT
        );""",

    """CREATE TABLE IF NOT EXISTS Users (
            user_id SERIAL PRIMARY KEY,
            login TEXT UNIQUE NOT NULL, 
            password TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        );""",

    """CREATE TABLE IF NOT EXISTS Requests (
            request_id SERIAL PRIMARY KEY,
            link_id INT NOT NULL REFERENCES Links(link_id), 
            request_dt TIMESTAMP NOT NULL,
            user_id INT
        );""",

    """CREATE INDEX IF NOT EXISTS url_codes ON Links (
            short_code
        );""",
]

db = None

async def create_sql_database(conn_string):
    global db
    db = await asyncpg.connect(conn_string)

    for statement in create_table_statements:
        await db.execute(statement)
    

async def add_link_to_db(short_code, url, user_id, expires_at):
    await db.execute("""INSERT INTO Links (short_code, url, user_id, created_at, expires_at, active)
                            VALUES ($1,$2,$3,$4,$5,$6)""", short_code, url, user_id, datetime.datetime.now(), expires_at, 1)


async def get_link_from_db(short_code):
    url = None
    link_id = None
    user_id = None
    expires_at = None

    row = await db.fetchrow(""" SELECT url, link_id, user_id, expires_at FROM Links WHERE short_code = $1 AND active = 1""", short_code)
    
    if row is not None:
        url = row[0]
        link_id = row[1]
        user_id = row[2]
        expires_at = row[3]

    return link_id, url, user_id, expires_at


async def find_link_by_url(url):
    user_id = None
    short_code = None
    expires_at = None

    row = await db.fetchrow(""" SELECT user_id, short_code, expires_at FROM Links WHERE url = $1 AND active = 1""", url)

    if row is not None:
        user_id = row[0]
        short_code = row[1]
        expires_at = row[2]

    return user_id, short_code, expires_at


async def delete_link_from_db(link_id):
    await db.execute("""UPDATE Links
                    SET active = 0
                    WHERE link_id = $1;""", link_id)


async def register_user_to_db(login, password):
    await db.execute("""INSERT INTO Users (login, password, created_at)
                              VALUES ($1,$2,$3)""", login, password, datetime.datetime.now())
        

async def get_user_by_login_db(login):
    user_id = None

    row = await db.fetchrow(f""" SELECT user_id FROM Users WHERE login = $1 """, login)

    if row is not None:
        user_id = row[0]

    return user_id


async def get_user_by_login_password_db(login, password):
    user_id = None

    row = await db.fetchrow(f""" SELECT user_id FROM Users WHERE login = $1 AND password = $2""", login, password)

    if row is not None:
        user_id = row[0]

    return user_id


async def log_request_to_db(link_id, user_id):
    await db.execute("""INSERT INTO Requests (link_id, user_id, request_dt)
                              VALUES ($1,$2,$3)""", link_id, user_id, datetime.datetime.now())
    

async def extend_link_life_db(link_id):
    await db.execute("""UPDATE Links
                    SET active = $2
                    WHERE link_id = $1;""", link_id, datetime.datetime.now() + datetime.timedelta(days=3))
        

async def get_stats_from_db(link_id): 
    request_count = 0
    latest_request = None
    created_at = None

    row = await db.fetchrow("""SELECT COUNT(DISTINCT(request_id)) FROM Requests WHERE link_id = $1""", link_id)
    if row is not None:
        request_count = row[0]

    row = await db.fetchrow("""SELECT MAX(request_dt) FROM Requests WHERE link_id = $1""", link_id)
    if row is not None:
        latest_request = row[0]

    row = await db.fetchrow("""SELECT created_at FROM Links WHERE link_id = $1""", link_id)
    if row is not None:
        created_at = row[0]

    return request_count, latest_request, created_at


async def get_all_user_links(user_id):
    data = []
    rows = await db.fetch(f"""SELECT link_id, short_code, url, expires_at, active FROM Links WHERE user_id = $1""", user_id)

    for row in rows:
        link_stats = await get_stats_from_db(row[0])
        cur_item = {'link_id': row[0], 'short_code': row[1], 'url': row[2],
                     'expires_at': row[3], 'active': row[4], 'request_count': link_stats[0],
                       'latest_request': link_stats[1], 'created_at': link_stats[2]}
        
        data.append(cur_item)
        
    return data


async def get_active_codes():
    codes = []
    rows = await db.fetch(f"""SELECT short_code FROM Links WHERE active = 1""")

    for row in rows:
        codes.append(row[0])

    return codes