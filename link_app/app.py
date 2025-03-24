import datetime
from random import choice
from string import ascii_lowercase

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import RedirectResponse

from pydantic import BaseModel
from typing import Annotated, Optional

import link_app.db 
import link_app.users


class UserData(BaseModel):
    login: str
    password: str

class UpdateLinkData(BaseModel):
    url: str

class OptionalHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        from fastapi import status
        try:
            r = await super().__call__(request)
            credentials = r
        except HTTPException as ex:
            assert ex.status_code == status.HTTP_403_FORBIDDEN, ex
            credentials = None
        return credentials


app = FastAPI()

security = HTTPBearer()
opt_security = OptionalHTTPBearer()

@app.on_event("startup")
async def startup():
    await link_app.db.create_sql_database()


@app.post("/links/shorten")
async def create_link(url, credentials: Annotated[HTTPAuthorizationCredentials, Depends(opt_security)],
                 custom_alias=None, expires_at=None):
    
    token = None
    if credentials is not None:
        token = credentials.credentials

    if custom_alias is None:
        used_codes = await link_app.db.get_active_codes()
        custom_alias = ''.join(choice(ascii_lowercase) for i in range(12))
        while custom_alias in used_codes:
            custom_alias = ''.join(choice(ascii_lowercase) for i in range(12))
        
    
    if expires_at is None:
        expires_at = datetime.datetime.now() + datetime.timedelta(days=7)
    else:
        expires_at = datetime.datetime.fromisoformat(expires_at)

    if token is None:
        user_id = None
    else:
        user_id = await link_app.users.current_user(token)


    link_id, _, _, _ = await link_app.db.get_link_from_db(custom_alias)

    if link_id is not None:
        raise HTTPException(status_code=400, detail='Sorry, this shortcode is already in use')

    try:
        await link_app.db.add_link_to_db(custom_alias, url, user_id, expires_at)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {'short_code': custom_alias, 'expires_at': expires_at}


@app.get("/links/{short_code}")
async def use_link(short_code):
    link_id, url, user_id, expires_at = await link_app.db.get_link_from_db(short_code)

    if link_id is None:
        raise HTTPException(status_code=404, detail="Link does not exist")
    
    if datetime.datetime.now() > expires_at:
        raise HTTPException(status_code=404, detail="Link expired")
    
    await link_app.db.log_request_to_db(link_id, user_id)
    
    return RedirectResponse(url)


@app.delete("/links/{short_code}")
async def delete_link(short_code, credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):

    token = credentials.credentials

    curr_user_id = await link_app.users.current_user(token)
    if curr_user_id is None:
        raise HTTPException(status_code=401, detail="User unknown")

    link_id, url, user_id, expires_at = await link_app.db.get_link_from_db(short_code)

    if datetime.datetime.now() > expires_at:
        raise HTTPException(status_code=404, detail="Link expired")
    
    if curr_user_id != user_id:
        raise HTTPException(status_code=403, detail="Wrong user. Permission Denied")
    
    try:
        await link_app.db.delete_link_from_db(link_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return None


@app.put("/links/{short_code}")
async def update_link(short_code, payload:UpdateLinkData,
                 credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    
    token = credentials.credentials
    url = payload.url

    curr_user_id = await link_app.users.current_user(token)
    if curr_user_id is None:
        raise HTTPException(status_code=401, detail="User unknown")

    link_id, old_url, user_id, expires_at = await link_app.db.get_link_from_db(short_code)

    if link_id is None:
        raise HTTPException(status_code=404, detail="Short link does not exist")

    if datetime.datetime.now() > expires_at:
        raise HTTPException(status_code=404, detail="Link expired")
    
    if curr_user_id != user_id:
        raise HTTPException(status_code=403, detail="Wrong user. Permission Denied")

    expires_at = datetime.datetime.now() + datetime.timedelta(days=7)
    
    try:
        await link_app.db.delete_link_from_db(link_id)
        await link_app.db.add_link_to_db(short_code, url, user_id, expires_at)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/links/{short_code}/stats")
async def get_stats(short_code):
    link_id, _, _, _ =  await link_app.db.get_link_from_db(short_code)

    if link_id is None:
        raise HTTPException(status_code=404, detail="Short link does not exist")
    
    request_count, latest_request, reg_user_count, created_at = await link_app.db.get_stats_from_db(link_id)

    return {'request_count': request_count, 'last_request': latest_request, 'reg_user_count': reg_user_count, 'created_at': created_at}


@app.get("/search")
async def search_link(original_url):
    user_id, short_code, expires_at = await link_app.db.find_link_by_url(original_url)
    if short_code is None:
        raise HTTPException(status_code=404, detail="No url link") 

    if datetime.datetime.now() > expires_at:
        raise HTTPException(status_code=404, detail="Link expired") 
    
    return {'short_code': short_code}


@app.post("/auth/register")
async def register_user(payload: UserData):

    token, err = await link_app.users.register_user(payload.login, payload.password)

    if err != None:
        raise HTTPException(status_code=400, detail=err)

    return {'token': token}


@app.post("/auth/login")
async def login_user(payload:UserData):

    token = await link_app.users.login_user(payload.login, payload.password)

    if token is None:
        raise HTTPException(status_code=401, detail="Login/Password is wronk")
    
    return {'token': token}