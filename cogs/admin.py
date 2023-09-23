import discord.ext.commands.errors
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def reload(self, ctx, message):
        try:
            await self.bot.reload_extension(f"cogs.{message.lower()}")
            await ctx.send(f"{message} cog has successfully been reloaded :)")

        except discord.ext.commands.errors.ExtensionNotLoaded:
            await ctx.send(f"{message} cog has failed to be reloaded :(")



async def setup(bot):
    await bot.add_cog(Admin(bot))
