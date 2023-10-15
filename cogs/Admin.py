import os
import sys
import subprocess
import importlib
import discord.ext.commands.errors
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """@commands.command()
    async def logs(self, ctx):
        filename = "logs/logs.txt"
        sys.stdout.close()
        await ctx.send(file=discord.File(filename))

        sys.stdout = open('logs/logs.txt', 'a')
        sys.stderr = sys.stdout"""

    def restart_program2(self):
        command_string = "python main2.py > output.txt 2>&1"
        try:
            result = subprocess.run(command_string, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, None, str(e)

    def restart_program(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)

    @commands.command(hidden=True)
    async def restart(self, ctx):
        await ctx.send("Restarting bot...")
        self.restart_program2()

    @commands.command(hidden=True)
    async def reload(self, ctx, message):
        try:
            await self.bot.unload_extension(f"cogs.{message}")
            await self.bot.load_extension(f"cogs.{message}")
            await ctx.send(f"{message} cog has successfully been reloaded :)")

        except (discord.ext.commands.errors.ExtensionNotLoaded, discord.ext.commands.errors.CommandInvokeError) as e:
            print(e)
            await ctx.send(f"{message} cog has failed to be reloaded :(")

    @commands.command(hidden=True)
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
