import asyncio
import json

from discord import Embed
from discord.ext import commands
from osrs.hiscores_stuff.hiscores import get_boss_kc
from osrs.spreadsheets.google_sheet_inputter import inputter
from osrs.hiscores_stuff.boss_name_getter import main as boss_name
from util.attachment_reader import ctx_attachment_reader as reader
from util.daily_task import run_daily_task
import textdistance


class Runescape(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spreadsheet = False
        asyncio.create_task(self.spreadsheet_loop())

        with open("storage/osrs_bosses.json", "r") as f:
            self.boss_dict = json.load(f)

        with open('storage/league.json', 'r') as f:
            self.gamer_dict = json.load(f)


    @commands.command()
    async def test(self, ctx):
        print(self.spreadsheet)

    @commands.command()
    async def osrs(self, ctx, *args):
        gamer = " ".join(args)
        gamers_id = str(ctx.author.id)

        user_dict = self.gamer_dict['users'].get(gamers_id, {})
        user_dict['osrs'] = gamer
        self.gamer_dict['users'][gamers_id] = user_dict

        with open('storage/league.json', 'w') as f:
            json.dump(self.gamer_dict, f, indent=2)

        return await ctx.send(f"Osrs account `{gamer}` successfully added as your account")

    @commands.command(aliases=['bj'])
    async def boss_json(self, ctx):
        boss_json = await reader(ctx)
        with open("storage/osrs_bosses.json", "w") as f:
            json.dump(boss_json, f, indent=2)

        return await ctx.send("All done!")

    @commands.command(aliases=['kc'])
    async def boss_kc(self, ctx, *args):
        raw_info = " ".join(args)
        gamer = None

        try:
            dash_index = raw_info.index('-')
            boss = raw_info[:dash_index].strip()
            gamer = raw_info[dash_index + 2:].strip()

        except ValueError:
            boss = raw_info

        if gamer is None:

            try:
                gamer = self.gamer_dict['users'][str(ctx.author.id)]['osrs']

            except KeyError:
                return await ctx.send("Either add your osrs account to the bot or add '- (account name)' after the boss")

        boss = await self.boss_spell_check(boss)

        status, stats = await self.look_up_boss_kc(gamer)

        if status != 200:
            return await ctx.send("User does not exist")

        try:
            kc = stats[boss]['kc']
            rank = stats[boss]['rank']

        except KeyError:
            kc = 0
            rank = "Unranked"

        embed_msg = Embed(
            title=f'{gamer} - {boss}',
            type='rich',
            description="",
            colour=self.boss_dict[boss]["COLOR"]
        )

        # embed_msg.set_image(url=self.boss_dict[boss]["PNG"])
        embed_msg.set_thumbnail(url=self.boss_dict[boss]["PNG"])
        embed_msg.add_field(name='Kill count', value=f"{kc:,}", inline=True)
        embed_msg.add_field(name='Rank', value=f"{rank:,}", inline=True)

        return await ctx.send(embed=embed_msg)

    @commands.command(aliases=["boss"])
    async def manually_update_boss_name(self, ctx):
        await boss_name()
        return await ctx.send("All done!")

    @commands.command(aliases=["spread"])
    async def manually_update_spreadsheet(self, ctx):
        await self.run_spreadsheets()
        return await ctx.send("All done!")

    async def spreadsheet_loop(self):
        await self.bot.wait_until_ready()
        while self is self.bot.get_cog('Runescape'):
            self.spreadsheet = True
            await run_daily_task('08:00:00')
            await self.bot.get_user(self.bot.settings.moist_id).send("I am gonna update the spreadsheets now :D")
            await self.run_spreadsheets()

    async def run_spreadsheets(self):
        await inputter("The Whisperer", "whisperer kc", compare_rank=1)
        await inputter("The Leviathan", "leviathan kc", compare_rank=1, main="hemeonc")
        await inputter("Duke Sucellus", "duke kc", extra="hemeonc", compare_rank=1000)
        await inputter("Tombs of Amascut: Expert Mode", "toa expert kc", extra="HemeOnc")

    async def look_up_boss_kc(self, name):
        status, stats = await get_boss_kc(name)
        if status != 200:
            return status, None

        return status, stats

    async def boss_spell_check(self, boss):
        distances = []

        for real_boss in self.boss_dict:

            if 'ALIAS' in self.boss_dict[real_boss]:
                boss_alias = self.boss_dict[real_boss]['ALIAS']

                for alias in boss_alias:
                    if alias in boss:
                        return real_boss

            distances.append([real_boss, textdistance.Levenshtein()(real_boss, boss)])

        return sorted(distances, key=lambda x: x[1])[0][0]


async def setup(bot):
    await bot.add_cog(Runescape(bot))
