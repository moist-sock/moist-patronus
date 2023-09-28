import aiohttp


async def request(url, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, **kwargs) as r:
            if r.status != 200:
                return r.status, None

            content_type = r.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return r.status, await r.json()

            return r.status, await r.text()
