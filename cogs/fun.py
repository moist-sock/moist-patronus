import discord
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def testy(self, ctx):
        print(ctx.message.content)
        await ctx.send("yes youd testy")


async def setup(bot):
    await bot.add_cog(Fun(bot))
