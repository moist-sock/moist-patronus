from discord.ext import commands
from util.async_request import request
from util.store_test_json import store_test


class Chess(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(Chess(bot))
