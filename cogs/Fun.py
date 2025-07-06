import logging
import os

import discord
import textdistance
from discord import app_commands
from discord.ext import commands
from util.time_functions import run_daily_task
import asyncio
import json


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jason_gm = asyncio.create_task(self.annoy_jason())

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            # message = str(ctx.message.content).lower()
            return

        elif isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
            await ctx.send(f"Please wait {error.retry_after:.2f} seconds before using this command again.")
            return

        raise error

    # noinspection PyUnresolvedReferences
    @app_commands.command(name="louie", description="task list for louie")
    @app_commands.describe(options='Options to choose from')
    @app_commands.choices(options=[
        discord.app_commands.Choice(name='View', value=1),
        discord.app_commands.Choice(name='Add', value=2),
        discord.app_commands.Choice(name='Remove', value=3)
    ])
    @app_commands.guild_only()
    async def louie_tasks(self, interaction: discord.Interaction, options: discord.app_commands.Choice[int], task: str=None):
        try:
            with open("storage/louie_tasks.json", "r") as f:
                list_of_tasks = json.load(f)

        except FileNotFoundError:
            with open("storage/louie_tasks.json", "w") as f:
                json.dump([], f, indent=2)
            list_of_tasks = []

        match options.value:
            case 1:
                if not list_of_tasks:
                    list_of_tasks = ["There are no tasks right now :("]
                output_msg = "\n".join(list_of_tasks)
                return await interaction.response.send_message(output_msg)

            case 2:
                if task is None:
                    return await interaction.response.send_message("Type a task to add")

                elif task in list_of_tasks:
                    return await interaction.response.send_message("No! That task is already in there")

                list_of_tasks.append(task)
                with open("storage/louie_tasks.json", "w") as f:
                    json.dump(list_of_tasks, f, indent=2)
                return await interaction.response.send_message("Task has successfully been added\n" + "\n".join(list_of_tasks))

            case 3:
                if task is None:
                    return await interaction.response.send_message("Type a task to remove")
                task = self.spell_check(task, list_of_tasks)
                list_of_tasks.remove(task)
                with open("storage/louie_tasks.json", "w") as f:
                    json.dump(list_of_tasks, f, indent=2)
                return await interaction.response.send_message(f"{task}\n has successfully been removed")

    def spell_check(self, thing_that_need_spellcheck, list_to_use):
        distances = []

        for real_thing_in_list in list_to_use:
            distances.append([real_thing_in_list, textdistance.Levenshtein()(real_thing_in_list.lower(), thing_that_need_spellcheck)])

        return sorted(distances, key=lambda x: x[1])[0][0]

    async def annoy_jason(self):
        await self.bot.wait_until_ready()
        while self is self.bot.get_cog('Fun'):
            await run_daily_task('08:00:00', "US/Mountain")
            await self.say_good_morning()

    async def say_good_morning(self):
        jason_id = 150021270426091520
        await self.bot.get_user(jason_id).send("good morning to you and to jarvis... jerk it a little")
        await self.bot.get_user(272945366029172748).send("i said good morning to jason")


async def setup(bot):
    await bot.add_cog(Fun(bot))
