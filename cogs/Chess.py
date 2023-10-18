from discord.ext import commands
from util.async_request import request
from util.store_test_json import store_test


class Chess(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def chess(self, ctx):
        username = "moistsockk"
        url = f"https://api.chess.com/pub/player/{username}/matches"

        status, stuff = await request(url)

        if status != 200:
            print(status)

        store_test(stuff)

        await ctx.send("all done")


async def setup(bot):
    await bot.add_cog(Chess(bot))
