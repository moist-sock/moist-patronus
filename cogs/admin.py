import subprocess
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

    @commands.command()
    async def update(self, ctx):
        repository_url = "https://github.com/moist-sock/moist-patronus"

        try:
            subprocess.run(["git", "pull", repository_url], check=True)
            print("Code updated successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error updating code: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


async def setup(bot):
    await bot.add_cog(Admin(bot))
