import os
import sys
import subprocess
import discord.ext.commands.errors
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def restart_program(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)

    @commands.command()
    async def restart(self, ctx):
        await ctx.send("Restarting bot...")
        self.restart_program()

    @commands.command()
    async def reload(self, ctx, message):
        try:
            await self.bot.reload_extension(f"cogs.{message.lower()}")
            await ctx.send(f"{message} cog has successfully been reloaded :)")

        except (discord.ext.commands.errors.ExtensionNotLoaded, discord.ext.commands.errors.CommandInvokeError) as e:
            print(e)
            await ctx.send(f"{message} cog has failed to be reloaded :(")

    @commands.command()
    async def update(self, ctx):
        repository_url = "https://github.com/moist-sock/moist-patronus"

        try:
            subprocess.run(["git", "pull", repository_url], check=True)
            # self.bot.logger("Code updated successfully.")
            await ctx.send("Code updated successfully.")

        except subprocess.CalledProcessError as e:
            # self.bot.logger.info(f"Error updating code: {e}")
            await ctx.send("I can't :(")

        except Exception as e:
            # self.bot.logger(f"An unexpected error occurred: {e}")
            await ctx.send("I can't :(")


async def setup(bot):
    await bot.add_cog(Admin(bot))
