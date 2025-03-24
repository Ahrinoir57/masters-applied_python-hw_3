import uuid
from typing import Optional
import jwt
import datetime

import link_app
import link_app.db

salt = "My tears"

async def register_user(login, password):
    if password is None:
        print('Password not good')
        return None, 'bad_password'
    
    try:
        await link_app.db.register_user_to_db(login, password)
    except Exception as e:
        print(str(e))
        print('Login is not unique')
        return None, 'repeating_login'

    expires_at = str(datetime.datetime.now() + datetime.timedelta(hours=1))

    encoded_jwt = jwt.encode({"login": login, 'expires_at': expires_at}, salt, algorithm="HS256")

    return encoded_jwt, None


async def login_user(login, password):
    user_id = await link_app.db.get_user_by_login_password_db(login, password)

    if user_id is None:
        print('Wrong login/password')
        return None

    expires_at = str(datetime.datetime.now() + datetime.timedelta(hours=1))

    encoded_jwt = jwt.encode({"login": login, 'expires_at': expires_at}, salt, algorithm="HS256")
    
    return encoded_jwt


async def current_user(token):

    try:
        decoded_token = jwt.decode(token, salt, algorithms=["HS256"])
        login = decoded_token['login']
        expires_at = decoded_token['expires_at']
    except Exception as e:
        print('Invalid token')
        return None

    if expires_at < str(datetime.datetime.now()):
        print('Expired token')
        return None

    user_id = await link_app.db.get_user_by_login_db(login)

    if user_id is None:
        print('Invalid login')

    return user_id
