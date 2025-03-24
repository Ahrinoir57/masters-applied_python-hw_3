import aiosqlite
import datetime
import asyncio


async def clear_expired_links():
    async with aiosqlite.connect("./database/test.db") as db:
        cursor = await db.cursor()
        await cursor.execute(f"""UPDATE Links
                        SET active = 0
                        WHERE expires_at < ?;""", (str(datetime.datetime.now()), ))
        await db.commit()
        await cursor.close()



if __name__ == '__main__':
    asyncio.run(clear_expired_links())