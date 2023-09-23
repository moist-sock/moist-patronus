import aiohttp

SUCCESS = 200


async def request(url, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, **kwargs) as r:
            if r.status is SUCCESS:  # A request status code of 200 just means success
                return r.status, await r.json()
            else:
                return r.status, None
