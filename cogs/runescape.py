from discord.ext import commands
from util.daily_task import run_daily_task
from osrs.hiscores_stuff.hiscores import get_boss_kc
from osrs.spreadsheets.google_sheet_inputter import inputter
from osrs.hiscores_stuff.boss_name_getter import main as boss_name


class Runescape(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spreadsheet = False

    @commands.command()
    async def lookup(self, ctx, *args):
        name = " ".join(args)
        status, stats = await get_boss_kc(name)
        if status != 200:
            return print("bad name")

        print(stats)

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
            await self.run_spreadsheets()

    async def run_spreadsheets(self):
        await inputter("The Whisperer", "whisperer kc", compare_rank=1)
        await inputter("The Leviathan", "leviathan kc", compare_rank=1, main="hemeonc")
        await inputter("Duke Sucellus", "duke kc", extra="hemeonc", compare_rank=1000)
        await inputter("Tombs of Amascut: Expert Mode", "Copy of toa expert kc", extra="HemeOnc")


async def setup(bot):
    await bot.add_cog(Runescape(bot))
