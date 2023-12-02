from discord.ext import commands
from util.async_request import request
import json
import discord


class Blazer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open("storage/task_id.json", "r") as f:
            self.task_ids = json.load(f)

        self.headers = {"User-Agent": "Message me on discord - moists0ck"}

    async def blazer_api_request(self, url):
        return await request(url, headers=self.headers)

    @commands.command(aliases=["surprise"])
    async def task(self, ctx, *args):
        test = " ".join(args)
        if (ctx.author.id == self.bot.settings.moist_id) != (test == "other"):
            account1 = "purple mouse"
            account2 = "NEX GOBLIN 7"

        else:
            account1 = "NEX GOBLIN 7"
            account2 = "purple mouse"

        account1_url = f"https://sync.runescape.wiki/runelite/player/{account1}/TRAILBLAZER_RELOADED_LEAGUE"
        account2_url = f"https://sync.runescape.wiki/runelite/player/{account2}/TRAILBLAZER_RELOADED_LEAGUE"

        status, account1_dict = await self.blazer_api_request(account1_url)

        if status != 200:
            print(f"{status} error with {account1} in trailblazer task command")
            return

        status, account2_dict = await self.blazer_api_request(account2_url)

        if status != 200:
            print(f"{status} error with {account2} in trailblazer task command")
            return

        account1_tasks = account1_dict['league_tasks'][:]
        account2_tasks = account2_dict['league_tasks'][:]

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

        msg = f'Tasks {account2}({points[1]}) has done but {account1}({points[0]}) hasnt\n' \
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


async def setup(bot):
    await bot.add_cog(Blazer(bot))
