import json

from discord.ext import commands
from util.daily_task import run_daily_task
from osrs.hiscores_stuff.hiscores import get_boss_kc
from osrs.spreadsheets.google_sheet_inputter import inputter
from osrs.hiscores_stuff.boss_name_getter import main as boss_name
from util.settings import moist_id
import textdistance


class Runescape(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spreadsheet = False

    async def look_up_boss_kc(self, name):
        status, stats = await get_boss_kc(name)
        if status != 200:
            return status, None

        return status, stats

    async def boss_spell_check(self, boss):
        distances = []
        with open("osrs/hiscores_stuff/osrs_bosses.json", "r") as f:
            boss_list = json.load(f)

        for real_boss in boss_list:

            """if 'ALIAS' in champs.CHAMP_INFO[real_champion]:
                champion_alias = champs.CHAMP_INFO[real_champion]['ALIAS']

                for alias in champion_alias:
                    if alias in champion:
                        return real_champion"""

            distances.append([real_boss, textdistance.Levenshtein()(real_boss, boss)])

        return sorted(distances, key=lambda x: x[1])[0][0]

    @commands.command(aliases=['kc'])
    async def boss_kc(self, ctx, *args):
        raw_info = " ".join(args)
        dash_index = raw_info.index('-')
        boss = raw_info[:dash_index].strip()
        gamer = raw_info[dash_index + 2:].strip()

        boss = await self.boss_spell_check(boss)

        status, stats = await self.look_up_boss_kc(gamer)

        if status != 200:
            return await ctx.send("User does not exist")

        try:
            kc = stats[boss]['kc']

        except KeyError:
            kc = 0

        return await ctx.send(f"{boss} kc = {kc}")

    @commands.command(aliases=["boss"])
    async def manually_update_boss_name(self, ctx):
        await boss_name()

    @commands.command(aliases=["spread"])
    async def manually_update_spreadsheet(self, ctx):
        await self.run_spreadsheets()

    async def spreadsheets_loop(self):
        while True:
            self.spreadsheet = True
            await run_daily_task('08:00:00')
            await self.bot.get_user(moist_id).send("I am gonna update the spreadsheets now :D")
            await self.run_spreadsheets()

    async def run_spreadsheets(self):
        await inputter("The Whisperer", "whisperer kc", compare_rank=1)
        await inputter("The Leviathan", "leviathan kc", compare_rank=1, main="hemeonc")
        await inputter("Duke Sucellus", "duke kc", extra="hemeonc", compare_rank=1000)
        await inputter("Tombs of Amascut: Expert Mode", "toa expert kc", extra="HemeOnc")


async def setup(bot):
    await bot.add_cog(Runescape(bot))
