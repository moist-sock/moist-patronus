import datetime
import json

import textdistance
from discord import Embed
from discord.ext import commands

from util.async_request import request
from util.store_test_json import store_test
from util.time_functions import time_ago


class Getracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.headers = {"User-Agent": "Discord bot for item price look up - moists0ck"}

        with open("storage/osrs_items.json", "r") as f:
            self.items = json.load(f)

        with open("storage/osrs_item_id_dict.json", "r") as f:
            self.items_id = json.load(f)

    async def ge_api_request(self, url):
        return await request(url, headers=self.headers)

    @commands.command(aliases=['p'])
    async def price(self, ctx, *args):
        item_name = " ".join(args)
        distances = []

        for real_item in self.items:
            distances.append([real_item, textdistance.Levenshtein()(real_item.lower(), item_name)])

        item_name = sorted(distances, key=lambda x: x[1])[0][0]

        status, items_prices = await self.all_item_price_with_most_recent_transaction()

        if status != 200:
            print(status)
            return

        key = str(self.items[item_name]["id"])

        try:
            price_dict = items_prices["data"][key]

        except KeyError:
            return await ctx.send(f"`{item_name}`, is bad no price for you")

        embed_msg = Embed(title=item_name)

        lowtime = await time_ago(price_dict['lowTime'])
        hightime = await time_ago(price_dict['highTime'])

        embed_msg.set_thumbnail(url=f"https://oldschool.runescape.wiki/images/{item_name.replace(' ', '_')}_detail.png")
        embed_msg.add_field(name="Price high", value=f"{price_dict['high']:,}")
        embed_msg.add_field(name=f"Last insta buy", value=f"{hightime}")
        embed_msg.add_field(name="\u200b", value='\u200b', inline=False)
        embed_msg.add_field(name="Price low", value=f"{price_dict['low']:,}")
        embed_msg.add_field(name=f"Last insta sell", value=f"{lowtime}")

        return await ctx.send(embed=embed_msg)

    @commands.command(hidden=True)
    async def margin(self, ctx, volume=None):
        status, item_dict = await self.all_item_price_with_most_recent_transaction()
        status_two, item_volume_dict = await self.all_item_price_with_volume()

        if status != 200 or status_two != 200:
            print(status, status_two, "margin command error")
            return await ctx.send(f"some type of error")
        store_test(item_dict)
        item_prices = item_dict["data"]
        item_volume = item_volume_dict["data"]

        margin_dict = {}
        for item in item_prices:
            if item in ["9044", "9050"]:
                continue
            high_price = item_prices[item]["high"]
            low_price = item_prices[item]["low"]

            try:
                hightime = int(item_prices.get(item, {}).get("highTime", 0))
                lowtime = int(item_prices.get(item, {}).get("lowTime", 0))

            except TypeError:
                continue

            high_volume = item_volume.get(item, {}).get("highPriceVolume", 0)
            low_volume = item_volume.get(item, {}).get("lowPriceVolume", 0)
            total_volume = high_volume + low_volume

            if not (high_price and low_price):
                continue

            tax = high_price * 0.01

            if tax > 5_000_000:
                tax = 5_000_000

            margin_dict[item] = {"margin": int(high_price - low_price - tax),
                                 "high": high_price,
                                 "low": low_price,
                                 "volume": total_volume,
                                 "highTime": hightime,
                                 "lowTime": lowtime}

        margin_list = []

        for item in margin_dict:
            margin_list.append([self.items_id[str(item)],
                                margin_dict[item]["margin"],
                                margin_dict[item]["high"],
                                margin_dict[item]["low"],
                                margin_dict[item]["volume"],
                                margin_dict[item]["highTime"],
                                margin_dict[item]["lowTime"]])

        margin_list = sorted(margin_list, key=lambda x: x[1], reverse=True)

        current_time = datetime.datetime.utcnow()
        one_hour = datetime.timedelta(hours=1)
        one_hour_ago = current_time - one_hour

        top_20 = []
        if volume:
            volume = int(volume)
            for item in margin_list:
                if len(top_20) == 20:
                    break

                if one_hour_ago > datetime.datetime.utcfromtimestamp(item[5]) and one_hour_ago > datetime.datetime.utcfromtimestamp(item[6]):
                    continue

                if volume > item[4]:
                    continue

                top_20.append(item)

        else:
            for item in margin_list:
                if len(top_20) == 20:
                    break
                if "3rd age" in item[0]:
                    continue

                top_20.append(item)

        msg = ""
        count = 1
        for item in top_20:
            msg += f"{count}. {item[0]} - margin: **{item[1]:,}** high: **{item[2]:,}** low: **{item[3]:,}**\n"
            count += 1

        return await ctx.send(msg)

    @commands.command()
    async def old(self, ctx, page=1):
        page = int(page)
        page = (page - 1) * 20
        status, item_dict = await self.all_item_price_with_most_recent_transaction()

        if status != 200:
            print(status)
            return await ctx.send("error")
        item_prices = item_dict["data"]

        margin_dict = {}
        for item in item_prices:
            if item in ["9044", "9050"]:
                continue
            high_price = item_prices[item]["high"]
            low_price = item_prices[item]["low"]
            try:
                hightime = int(item_prices[item]['highTime'])
                lowtime = int(item_prices[item]["lowTime"])

            except TypeError:
                continue

            if not (high_price and low_price):
                continue

            margin_dict[item] = {"high": high_price,
                                 "low": low_price,
                                 "highTime": hightime,
                                 "lowTime": lowtime}

        margin_list = []
        for item in margin_dict:
            margin_list.append([self.items_id[str(item)],
                                margin_dict[item]["high"],
                                margin_dict[item]["low"],
                                margin_dict[item]["highTime"],
                                margin_dict[item]["lowTime"]])

        margin_list = sorted(margin_list, key=lambda x: x[4])

        count = 1
        count += page
        eternal_page = page
        msg = ""
        for item in margin_list:
            if page:
                page -= 1
                continue

            if count == 21 + eternal_page:
                break

            msg += f"{count}. {item[0]} - {await time_ago(item[4])}\n"
            count += 1

        return await ctx.send(msg)

    @commands.command(hidden=True)
    async def items(self, ctx):
        status, dict = await self.ge_api_request("https://prices.runescape.wiki/api/v1/osrs/mapping")

        store_test(dict)
        return await ctx.send("done")

    async def volume_look_up(self, item_id, time="5m"):
        url = f"https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep={time}&id={item_id}"

        return await self.ge_api_request(url)

    async def all_item_price_with_most_recent_transaction(self):
        return await self.ge_api_request("https://prices.runescape.wiki/api/v1/osrs/latest")

    async def all_item_price_with_volume(self):
        return await self.ge_api_request("https://prices.runescape.wiki/api/v1/osrs/5m")


async def setup(bot):
    await bot.add_cog(Getracker(bot))
