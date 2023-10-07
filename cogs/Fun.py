import logging
import os

from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            # message = str(ctx.message.content).lower()
            return
        raise error

    @commands.command(aliases=["find"], hidden=True)
    async def find_json_files(self, ctx):
        base_directory = r"C:\Users\duke\Documents\GitHub\moist-patronus"
        for root, dirs, files in os.walk(base_directory):
            if "site-packages" in root:
                continue
            for filename in files:
                # Check if the file has a .json extension
                if filename.endswith('.json') or filename.endswith('.txt'):
                    # Print the full path to the JSON file
                    json_file_path = os.path.join(root, filename)
                    print(json_file_path)


async def setup(bot):
    await bot.add_cog(Fun(bot))
