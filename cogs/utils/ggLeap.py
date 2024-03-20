import datetime
import logging
import aiohttp
import typing
import json

API_URL = "https://api.ggleap.com/beta"
log = logging.getLogger(__name__)

class JWT:
    def __init__(self) -> None:
        self.last_renewed = None
        self.value = None

    async def renew(self, auth: str) -> None:
        """Call's GGLeap's API to renew the JWT"""
        payload = f"{{\n  \"AuthToken\": \"{auth.strip()}\"\n}}"
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_URL}/authorization/public-api/auth", data=payload, headers={'Content-Type': 'application/json-patch+json'}) as resp:
                t = await resp.text()
                t = json.loads(t.strip())
                self.value = t["Jwt"]
                self.last_renewed = datetime.datetime.utcnow()
    
    @staticmethod
    def validate(func):
        """A check that verifies that the JWT isn't expired, and automatically
        renews it if it is. GGLeap API Docs reccomend that it's refreshed every 5 minutes,
        but this is refreshed only if it's 7.5 minutes old. No reason why
        I chose that in specific i guess. Anyways this does not modify the decorated
        functions arguments (except for the JWT object)"""
        async def _decorator(self, *args, **kwargs):
            expired_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=7, seconds=30) # 7.5 min
            log.info(f"jwt manager is {type(self.jwt_manager)}")
            if (self.jwt_manager.last_renewed is None) or (self.jwt_manager.last_renewed > expired_time):
                print("last_renewed was None or expired")
                await self.jwt_manager.renew(self.authkey)
            if self.jwt_manager.last_renewed < expired_time:
                #within the timeframe
                pass
            return await func(self, *args, **kwargs)
        return _decorator

class ggAPI:
    def __init__(self, jwt_manager: JWT, authkey: str):
        self.jwt_manager = jwt_manager
        self.authkey = authkey

    @JWT.validate
    async def do_get(self, endpoint: str, payload: typing.Union[dict, str] = None, header: str = "application/json"):
        headers = {"Content-Type": header, "Authorization": self.jwt_manager.value}
        resp = ""
        async with aiohttp.ClientSession() as session:
            print(f"payload is {type(payload)}")
            if not payload:
                async with session.get(f"{API_URL}{endpoint}", headers=headers) as resp:
                    print(1)
                    resp = await resp.text()
            else:
                async with session.get(f"{API_URL}{endpoint}", headers=headers, params=payload) as resp:
                    print(2)
                    resp = await resp.text()
        try: return json.loads(resp)
        except json.decoder.JSONDecodeError: return None

    async def get_user(self, username: str) -> typing.Union[dict, None]:
        payload = {"Username":username}
        return await self.do_get('/users/user-details', payload=payload)
    
    async def get_uuid(self, username: str):
        res = await self.get_user(username)
        if res is None: return None
        return res["User"]["Uuid"]
    
    async def get_time(self, username: str):
        uuid = await self.get_uuid(username)
        if uuid is None: return None
        return await self.do_get('/sessions/get-time', payload={"UserUuids[]": uuid})
    
    async def get_coins(self, uuid: str):
        payload = {"UserUuid":uuid}
        return await self.do_get('/coins/balance', payload=payload)
    
    async def all_games(self):
        return await self.do_get('/apps/get-enabled-apps-summary')
    
    async def all_pcs(self):
        return await self.do_get('/machines/get-all')