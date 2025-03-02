from discord.ext import commands
from util.async_request import request
import json
import discord
from discord import Embed, app_commands


class Echo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open("storage/echo_tasks.json", "r") as f:
            self.task_ids = json.load(f)

        self.headers = {"User-Agent": "Message me on discord - moists0ck"}

    async def blazer_api_request(self, url):
        return await request(url, headers=self.headers)

    @commands.command(aliases=["surprise"])
    async def task(self, ctx, *args):
        test = " ".join(args)
        if (ctx.author.id == self.bot.settings.moist_id) != (test == "other"):
            account1 = "moisty s0ck"
            account2 = "DetestQuests"

        else:
            account1 = "DetestQuests"
            account2 = "moisty s0ck"

        account1_url = f"https://sync.runescape.wiki/runelite/player/{account1}/RAGING_ECHOES_LEAGUE"
        account2_url = f"https://sync.runescape.wiki/runelite/player/{account2}/RAGING_ECHOES_LEAGUE"

        status, account1_dict = await self.blazer_api_request(account1_url)

        if status != 200:
            print(f"{status} error with {account1} in echo task command\n"
                  f"{account1_dict}")
            return

        status, account2_dict = await self.blazer_api_request(account2_url)

        if status != 200:
            print(f"{status} error with {account2} in echo task command")
            return

        account1_tasks = account1_dict['league_tasks'][:]
        account2_tasks = account2_dict['league_tasks'][:]

        account1_amount_of_taks = len(account1_tasks)
        account2_amount_of_taks = len(account2_tasks)

        accounts = [account1_tasks, account2_tasks]
        points = []
        for account in accounts:
            total_point = 0
            for task in account:
                task = str(task)
                point = int(self.task_ids[task]['value'])
                total_point += point

            points.append(total_point)

        for task in account1_dict['league_tasks']:
            if task in account2_dict['league_tasks']:
                account1_tasks.remove(task)
                account2_tasks.remove(task)

        diff_tasks_names = []
        total_point = 0
        for task in account2_tasks:
            task = str(task)
            point = int(self.task_ids[task]['value'])
            total_point += point
            diff_tasks_names.append([self.task_ids[task]['name'], point])

        diff_tasks_names.sort(key=lambda x: x[1], reverse=True)

        msg = f'Tasks {account2}({points[1]})[{account2_amount_of_taks}] has done but {account1}({points[0]})[{account1_amount_of_taks}] hasnt\n' \
              f'These tasks are worth a total of {total_point} points\n'
        for task in diff_tasks_names:
            msg += f"{task[1]} - {task[0]}\n"

        try:
            await ctx.send(msg)

        except discord.errors.HTTPException:
            raw_msg = msg.splitlines()

            msg_list = []
            while raw_msg:
                msg_short = ''

                while raw_msg and len(msg_short) + len(raw_msg[0]) + 1 < 2000:
                    line_to_add = f"{raw_msg.pop(0)}\n"
                    msg_short += line_to_add

                msg_list.append(msg_short)

            for short_msg in msg_list:
                await ctx.send(short_msg)

    @app_commands.command(name="task", description="compare tasks")
    @app_commands.guild_only()
    async def diaries(self, interaction: discord.Interaction, area: discord.app_commands.Choice[int],
                      tier: discord.app_commands.Choice[int],
                      gamer: str):
        pass


async def setup(bot):
    await bot.add_cog(Echo(bot))
