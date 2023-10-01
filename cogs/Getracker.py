from discord.ext import commands


class Getracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.headers = {"User-Agent": "Discord bot for item price look up - moists0ck"}


async def setup(bot):
    await bot.add_cog(Getracker(bot))
