import asyncio
import json
import textdistance

from datetime import datetime
from math import log, ceil
from discord import Embed
from discord.ext import commands
from osrs.hiscores_stuff.hiscores import get_boss_kc, get_stats
from osrs.spreadsheets.google_sheet_inputter import inputter
from osrs.xp import xp_dict
from osrs.hiscores_stuff.boss_name_getter import main as boss_name
from util.attachment_reader import ctx_attachment_reader as reader
from util.time_functions import run_daily_task


class NoName(Exception):
    async def message(self, ctx, sep):
        await ctx.send(
            f"Either add your account to the bot with !osrs or add '{sep} (account name)' after the first input")


class Runescape(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spreadsheet = asyncio.create_task(self.spreadsheet_loop())
        self.seperator = "/"

        with open("storage/osrs_bosses.json", "r") as f:
            self.boss_dict = json.load(f)

        with open('storage/league.json', 'r') as f:
            self.gamer_dict = json.load(f)

    @commands.command()
    async def funbox(self, ctx):
        return await ctx.send(
            '[{"regionId":15184,"regionX":26,"regionY":42,"z":1,"color":"#FFFFFF00"},{"regionId":15184,"regionX":24,"regionY":40,"z":1,"color":"#FFFFFF00"},{"regionId":15184,"regionX":23,"regionY":39,"z":1,"color":"#FF3AFF20"},{"regionId":15184,"regionX":26,"regionY":39,"z":1,"color":"#FF3AFF20"},{"regionId":15184,"regionX":29,"regionY":39,"z":1,"color":"#FF3AFF20"},{"regionId":15184,"regionX":29,"regionY":42,"z":1,"color":"#FF3AFF20"},{"regionId":15184,"regionX":29,"regionY":45,"z":1,"color":"#FF3AFF20"},{"regionId":15184,"regionX":26,"regionY":45,"z":1,"color":"#FF3AFF20"},{"regionId":15184,"regionX":23,"regionY":45,"z":1,"color":"#FF3AFF20"},{"regionId":15184,"regionX":23,"regionY":42,"z":1,"color":"#FF3AFF20"},{"regionId":15696,"regionX":32,"regionY":42,"z":1,"color":"#FFFFFF00"},{"regionId":15696,"regionX":37,"regionY":45,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":37,"regionY":44,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":37,"regionY":43,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":37,"regionY":42,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":37,"regionY":41,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":27,"regionY":45,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":27,"regionY":44,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":27,"regionY":43,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":27,"regionY":42,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":27,"regionY":41,"z":1,"color":"#FFFF0000"}]')

    @commands.command(aliases=["next"], hidden=True)
    async def next_level(self, ctx, *args):
        try:
            gamer, info = self.parse_input(ctx, args)

        except NoName:
            return await NoName.message(NoName(), ctx, self.seperator)

        print(type(info))

    @commands.command(aliases=["when"])
    async def when_calculator(self, ctx,
                              percent: str = commands.parameter(description="Percent as a whole number"),
                              rate: str = commands.parameter(description="Drop rate as a fraction")):
        """
        Sends the kc needed to reach the inputted percent chance for the inputted drop rate
        """
        try:
            if len(percent) <= 2:
                divide_by = 100

            else:
                divide_by = 10 ** (len(percent))

            probability = float(percent) / divide_by

        except (ValueError, IndexError):
            return await ctx.send("Error! example usage would be...\n"
                                  "!when percent rate\n"
                                  "!when 50 1/300")

        try:
            decimal_rate = eval(rate)  # Evaluate the rate string (e.g., "1/10" becomes 0.1)

        except ZeroDivisionError:
            return await ctx.send("Why divide by zero")

        kc_needed = log(1 - probability) / log(1 - decimal_rate)

        msg = f"{ceil(kc_needed)} kc for {probability * 100}% chance"

        return await ctx.send(msg)

    @commands.command(aliases=["drycalc", "dry"])
    async def dry_calculator(self, ctx, *args):

        try:
            current_kc = int(args[0])
            rate = args[1]

        except (ValueError, IndexError):
            return await ctx.send("Error! example usage would be...\n"
                                  "!dry kc rate\n"
                                  "!dry 10 1/100")

        try:
            decimal_rate = eval(rate)  # Evaluate the rate string (e.g., "1/10" becomes 0.1)

        except ZeroDivisionError:
            return await ctx.send("Why divide by zero")

        # Calculate the probability
        probability = 1 - (1 - decimal_rate) ** current_kc

        return await ctx.send(probability)

    @commands.command()
    async def max(self, ctx, *date):
        """Returns xp needed a day to max on certain date"""
        # jan 1 2024
        try:
            gamer, date = self.parse_input(ctx, date)

        except NoName:
            return await NoName.message(NoName(), ctx, self.seperator)

        try:
            date_object = datetime.strptime(date, "%b %d %Y")

        except ValueError:
            return await ctx.send("Bad date format - example format 'jan 1 2024'")

        days_til = date_object - datetime.utcnow()
        days_til = int(str(days_til.days))
        days_til += 1

        status, stats_dict = await get_stats(gamer)

        if status != 200:
            print(f"bad status error {status}")
            return

        xp_a_day = {}
        total_xp = 0
        for stat in stats_dict:
            if stats_dict[stat]["level"] >= 99:
                continue
            stat_xp = int((xp_dict["99"] - stats_dict[stat]["xp"]) / days_til) + 1
            total_xp += stat_xp
            xp_a_day[stat] = stat_xp

        xp_a_day["Total xp a day"] = total_xp

        embed_msg = Embed(title=f"Xp a day needed to max on {date}")

        for skill in xp_a_day:
            embed_msg.add_field(name=skill, value=f"{xp_a_day[skill]:,}", inline=True)

        return await ctx.send(embed=embed_msg)

    @commands.command()
    async def osrs(self, ctx, *args):
        """Set osrs account"""
        gamer = " ".join(args)
        gamers_id = str(ctx.author.id)

        user_dict = self.gamer_dict['users'].get(gamers_id, {})
        user_dict['osrs'] = gamer
        self.gamer_dict['users'][gamers_id] = user_dict

        with open('storage/league.json', 'w') as f:
            json.dump(self.gamer_dict, f, indent=2)

        return await ctx.send(f"Osrs account `{gamer}` successfully added as your account")

    @commands.command(aliases=['bj'], hidden=True)
    async def boss_json(self, ctx):
        boss_json = await reader(ctx)
        with open("storage/osrs_bosses.json", "w") as f:
            json.dump(boss_json, f, indent=2)

        return await ctx.send("All done!")

    @commands.command(aliases=['kc'])
    async def boss_kc(self, ctx, *args):
        try:
            gamer, raw_boss = self.parse_input(ctx, args)

        except NoName:
            return await NoName.message(NoName(), ctx, self.seperator)

        boss = await self.boss_spell_check(raw_boss)

        status, stats = await get_boss_kc(gamer)

        if status != 200:
            return await ctx.send(f"User {gamer} does not exist")

        try:
            kc = stats[boss]['kc']
            rank = f"{stats[boss]['rank']:,}"

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
        embed_msg.add_field(name='Rank', value=rank, inline=True)

        return await ctx.send(embed=embed_msg)

    def parse_input(self, ctx, args):
        raw_info = " ".join(args)
        gamer = None

        try:
            dash_index = raw_info.index(self.seperator)
            data2 = raw_info[:dash_index].strip()
            gamer = raw_info[dash_index + 2:].strip()

        except ValueError:
            data2 = raw_info

        if gamer is None:

            try:
                gamer = self.gamer_dict['users'][str(ctx.author.id)]['osrs']

            except KeyError:
                raise NoName

        return gamer, data2

    @commands.command(aliases=["boss"], hidden=True)
    async def manually_update_boss_name(self, ctx):
        await boss_name()
        return await ctx.send("All done!")

    @commands.command(aliases=["spread"], hidden=True)
    async def manually_update_spreadsheet(self, ctx):
        await self.run_spreadsheets()
        return await ctx.send("All done!")

    @commands.command(hidden=True)
    async def check(self, ctx):
        loop = "on"
        if self.spreadsheet.done():
            loop = "off"
        await ctx.send(f"spreadsheet loop is {loop}")

    async def spreadsheet_loop(self):
        await self.bot.wait_until_ready()
        while self is self.bot.get_cog('Runescape'):
            await run_daily_task('08:00:00')
            await self.bot.get_user(self.bot.settings.moist_id).send("Good morning!!\nI am gonna update the spreadsheets now :D")
            await self.bot.get_user(self.bot.settings.sarah_id).send("Good morning!!\nI am gonna update the spreadsheets now :D")
            await self.run_spreadsheets()

    async def run_spreadsheets(self):
        await inputter("The Whisperer", "whisperer kc", compare_rank=1)
        await inputter("The Leviathan", "leviathan kc", compare_rank=1, main="hemeonc")
        await inputter("Duke Sucellus", "duke kc", extra="hemeonc", compare_rank=1000)
        await inputter("Tombs of Amascut: Expert Mode", "toa expert kc", extra="HemeOnc")

    async def boss_spell_check(self, boss):
        distances = []

        for real_boss in self.boss_dict:

            if 'ALIAS' in self.boss_dict[real_boss]:
                boss_alias = self.boss_dict[real_boss]['ALIAS']

                for alias in boss_alias:
                    if alias in boss:
                        return real_boss

            distances.append([real_boss, textdistance.Levenshtein()(real_boss.lower(), boss)])

        return sorted(distances, key=lambda x: x[1])[0][0]


async def setup(bot):
    await bot.add_cog(Runescape(bot))
