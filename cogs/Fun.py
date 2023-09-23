import discord
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def testy(self, ctx):
        await ctx.send("yes you testy")


async def setup(bot):
    await bot.add_cog(Fun(bot))
