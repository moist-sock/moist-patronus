import asyncio
from datetime import datetime, timedelta
import json
import discord
import pytz

from discord import Embed, app_commands
from discord.ext import commands

from util.async_request import request
from util.store_test_json import store_test


class Almanax(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open("storage/almanax.json", "r") as f:
            self.offerings_dict = json.load(f)

    @app_commands.command(name="offering", description="Shows offering for the day")
    @app_commands.guild_only()
    async def offering_slash(self, interaction: discord.Interaction,
                             extra: int = 0):
        extra += 1  # the loop later will not work if number is zero and its easier for me to type the amount of extra days as just that instead of including current day + extra
        utc_plus_7 = pytz.timezone('Africa/Johannesburg')
        now = datetime.now(utc_plus_7)

        msg = ""
        for day in range(extra):
            day_requested = now + timedelta(days=day)

            month = day_requested.strftime("%B")
            day = day_requested.strftime("%d")
            day = str(int(day))  # without this single digit days 1-9 dont line up with the dictionary 01 vs 1
            offering_and_market = self.offerings_dict[month][day]

            msg += f"{offering_and_market[0]} - {offering_and_market[1]} - {month} {day}\n"

        await interaction.response.send_message(msg)


async def setup(bot):
    await bot.add_cog(Almanax(bot))
