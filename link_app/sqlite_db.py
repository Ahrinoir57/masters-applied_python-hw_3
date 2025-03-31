import aiosqlite
import os
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "../database/test.db")

create_table_statements = [ 
    """CREATE TABLE IF NOT EXISTS Links (
            link_id INTEGER PRIMARY KEY, 
            short_code TEXT NOT NULL, 
            url TEXT NOT NULL,
            user_id INT,
            created_at TEXT,
            expires_at TEXT, 
            active INT
        );""",

    """CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL, 
            password TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES links (user_id)
        );""",

    """CREATE TABLE IF NOT EXISTS Requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id INT NOT NULL, 
            request_dt TEXT NOT NULL,
            user_id INT,
            FOREIGN KEY (link_id) REFERENCES links (link_id)
        );""",

    """CREATE INDEX IF NOT EXISTS url_codes ON Links (
            short_code
        );""",
]

async def create_sql_database():
    if not os.path.isdir('./database/'):
        print('Creating database')

        os.makedirs('./database/')
        async with aiosqlite.connect(db_path) as conn:
            for statement in create_table_statements:
                await conn.execute(statement)

            await conn.commit()


async def add_link_to_db(short_code, url, user_id, expires_at):
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.cursor()
        await cursor.execute("""INSERT INTO Links (short_code, url, user_id, created_at, expires_at, active)
                              VALUES (?,?,?,?,?,?)""", (short_code, url, user_id, str(datetime.datetime.now()), expires_at, 1))
        await db.commit()
        await cursor.close()


async def get_link_from_db(short_code):
    url = None
    link_id = None
    user_id = None
    expires_at = None
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(f""" SELECT url, link_id, user_id, expires_at FROM Links WHERE short_code = ? AND active = 1""", (short_code,)) as cursor:
            async for row in cursor:
                url = row[0]
                link_id = row[1]
                user_id = row[2] 
                expires_at = row[3]

    return link_id, url, user_id, expires_at


async def find_link_by_url(url):
    user_id = None
    short_code = None
    expires_at = None
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(f""" SELECT user_id, short_code, expires_at FROM Links WHERE url = ? AND active = 1""", (url, )) as cursor:
            async for row in cursor:
                print(row)
                user_id = row[0]
                short_code = row[1]
                expires_at = row[2]

    return user_id, short_code, expires_at


async def delete_link_from_db(link_id):
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.cursor()
        await cursor.execute(f"""UPDATE Links
                        SET active = 0 
                        WHERE link_id = ?;""", (link_id,))
        await db.commit()
        await cursor.close()


async def register_user_to_db(login, password):
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.cursor()
        await cursor.execute("""INSERT INTO Users (login, password, created_at)
                              VALUES (?,?,?)""", (login, password, str(datetime.datetime.now())))
        await db.commit()
        await cursor.close()


async def get_user_by_login_db(login):
    user_id = None
    
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(f""" SELECT user_id FROM Users WHERE login = ? """, (login,)) as cursor:
            async for row in cursor:
                user_id = row[0]

    return user_id


async def get_user_by_login_password_db(login, password):
    user_id = None
    
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(f"""SELECT user_id FROM Users WHERE login = ? AND password = ? """, (login, password)) as cursor:
            async for row in cursor:
                user_id = row[0]

    return user_id


async def log_request_to_db(link_id, user_id):
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.cursor()
        await cursor.execute("""INSERT INTO Requests (link_id, user_id, request_dt)
                              VALUES (?,?,?)""", (link_id, user_id, str(datetime.datetime.now())))
        await db.commit()
        await cursor.close()


async def get_stats_from_db(link_id): 
    request_count = 0
    latest_request = None
    created_at = None

    async with aiosqlite.connect(db_path) as db:
        async with db.execute(f"""SELECT COUNT(DISTINCT(request_id)) FROM Requests WHERE link_id = ?""", (link_id,)) as cursor:
            async for row in cursor:
                request_count = row[0]
        
        async with db.execute(f"""SELECT MAX(request_dt) FROM Requests WHERE link_id = ?""", (link_id,)) as cursor:
            async for row in cursor:
                latest_request = row[0]

        async with db.execute(f"""SELECT created_at  FROM Links WHERE link_id = ?""", (link_id,)) as cursor:
            async for row in cursor:
                created_at = row[0]
    

    return request_count, latest_request, created_at


async def get_active_codes():
    codes = []
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(f"""SELECT short_code FROM Links WHERE active = 1""") as cursor:
            async for row in cursor:
                codes.append(row[0])

    return codes
