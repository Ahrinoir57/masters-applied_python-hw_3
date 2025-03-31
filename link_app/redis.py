import aioredis

redis = None

async def create_redis():
    global redis
    redis = await aioredis.from_url("redis://redis")


async def cache_token(login, password, value):
    json_obj = {'login': login, 'password': password}
    key = str(json_obj)
    await redis.set(key, value, ex=3600)


async def get_token(login, password):
    json_obj = {'login': login, 'password': password}
    key = str(json_obj)
    await redis.get(key)