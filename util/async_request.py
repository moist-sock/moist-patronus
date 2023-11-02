import aiohttp
from io import BytesIO


async def request(url, ssl=True, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, ssl=ssl, **kwargs) as r:
            if r.status != 200:
                return r.status, None

            content_type = r.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return r.status, await r.json()

            if 'image/png' in content_type:
                image_data = BytesIO(await r.read())
                return r.status, image_data

            return r.status, await r.text()
