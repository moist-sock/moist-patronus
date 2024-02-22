import asyncio
import datetime
import json

import textdistance
from discord import Embed
from discord.ext import commands

from util.async_request import request
from util.store_test_json import store_test
from util.time_functions import time_ago, run_half_hourly_task, run_daily_task
from pprint import pprint


class Getracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.item_loop = asyncio.create_task(self.check_items())
        self.headers = {"User-Agent": "Discord bot for item price look up - moists0ck"}

        with open("storage/osrs_items.json", "r") as f:
            self.items = json.load(f)

        with open("storage/osrs_item_id_dict.json", "r") as f:
            self.items_id = json.load(f)

    async def ge_api_request(self, url):
        return await request(url, headers=self.headers)

    async def check_items(self):
        await self.bot.wait_until_ready()
        while self is self.bot.get_cog('Getracker'):
            await run_daily_task('08:00:30')
            await self.update_items()

    async def update_items(self):
        status, list_of_items = await request("https://prices.runescape.wiki/api/v1/osrs/mapping")

        if status != 200:
            print(f"error in def update_items, {status}")
            return

        item_dict = {}
        id_to_item = {}
        for item in list_of_items:
            item_dict[item["name"]] = {"examine": item.get("examine", None),
                                       "id": item.get("id", None),
                                       "members": item.get("members", None),
                                       "lowalch": item.get("lowalch", None),
                                       "limit": item.get("limit", None),
                                       "value": item.get("value", None),
                                       "highalch": item.get("highalch", None),
                                       "icon": item.get("icon", None)}
            id_to_item[item.get("id", "fart")] = item.get("name", "poop")

        if item_dict == self.items:
            return

        await self.bot.get_user(self.bot.settings.moist_id).send("New items were added to osrs!!")
        self.items = item_dict
        self.items_id = id_to_item

        with open("storage/osrs_items.json", "w") as f:
            json.dump(item_dict, f, indent=2)

        with open("storage/osrs_item_id_dict.json", "w") as f:
            json.dump(id_to_item, f, indent=2)

    @commands.command(aliases=['p'])
    async def price(self, ctx, *args):
        item_name = " ".join(args)
        distances = []

        for real_item in self.items:
            distances.append([real_item, textdistance.Levenshtein()(real_item.lower(), item_name)])

        item_name = sorted(distances, key=lambda x: x[1])[0][0]

        status, items_prices = await self.all_item_price_with_most_recent_transaction()

        if status != 200:
            print(f"error in !price {status}, args given = {item_name}")
            return await ctx.send("uh something went wrong in my code :(")

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

                if one_hour_ago > datetime.datetime.utcfromtimestamp(
                        item[5]) and one_hour_ago > datetime.datetime.utcfromtimestamp(item[6]):
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

    @commands.command()
    async def cry(self, ctx, *args):
        if args:
            check = args[0]

        else:
            check = False
        if check == "2":
            items_sold = {"inq": {"name": "Inquisitor's armour set",
                                  "price": 172_600_000,
                                  "id": 24488}
                          }

            items_bought = {"weapon_seed": {"price": 90_875_000,
                                            "amount": 100,
                                            "name": "Enhanced crystal weapon seed",
                                            "id": 25859}}
        else:
            items_sold = {"tbow": {"name": "Twisted bow",
                                   "price": 1_510_000_000,
                                   "id": 20997},
                          "shadow": {"price": 1_338_000_000,
                                     "name": "Tumeken's shadow (uncharged)",
                                     "id": 27277},
                          "acb": {"price": 51_480_000,
                                  "name": "Armadyl crossbow",
                                  "id": 11785},
                          "zvambs": {"price": 156_420_000,
                                     "name": "Zaryte vambraces",
                                     "id": 26235},
                          "masori": {"price": 222_750_000,
                                     "name": "Masori armour set (f)",
                                     "id": 27355},
                          "venny_bow": {"price": 26_081_101,
                                        "name": "Venator bow (uncharged)",
                                        "id": 27612},
                          "virtus_top": {"price": 72_634_844,
                                         "name": "Virtus robe top",
                                         "id": 26243},
                          "virtus_bottom": {"price": 30_135_600,
                                            "name": "Virtus robe bottom",
                                            "id": 26245}}

            items_bought = {"armour_seed": {"price": 4_054_568,
                                            "amount": 658,
                                            "name": "Crystal armour seed",
                                            "id": 23956},
                            "weapon_seed": {"price": 90_850_000,
                                            "amount": 8,
                                            "name": "Enhanced crystal weapon seed",
                                            "id": 25859}}

        status, items_prices = await self.all_item_price_with_most_recent_transaction()

        if status != 200:
            print(f"error in cry, {status}")
            return await ctx.send("error in api call")

        items_prices = items_prices["data"]

        lowprofit = 0
        highprofit = 0

        items_sold_msg = ""
        items_bought_msg = ""
        for key in items_sold.keys():
            items_sold[key]["currentlow"] = items_prices[str(items_sold[key]["id"])]["low"]
            items_sold[key]["currenthigh"] = items_prices[str(items_sold[key]["id"])]["high"]
            if check == "2":
                items_sold[key]["highprofit"] = (items_sold[key]["price"] - items_sold[key]["currentlow"]) * 50
                items_sold[key]["lowprofit"] = (items_sold[key]["price"] - items_sold[key]["currenthigh"]) * 50

            else:
                items_sold[key]["highprofit"] = items_sold[key]["price"] - items_sold[key]["currentlow"]
                items_sold[key]["lowprofit"] = items_sold[key]["price"] - items_sold[key]["currenthigh"]

            lowprofit += items_sold[key]["lowprofit"]
            highprofit += items_sold[key]["highprofit"]

            items_sold_msg += f"{items_sold[key]['name']}: {items_sold[key]['lowprofit']:,} | {items_sold[key]['highprofit']:,}\n"

        for key in items_bought.keys():
            lowprice = items_prices[str(items_bought[key]["id"])]["low"]
            highprice = items_prices[str(items_bought[key]["id"])]["high"]
            items_bought[key]["currentlow"] = lowprice
            items_bought[key]["currenthigh"] = highprice
            items_bought[key]["lowprofit"] = int(lowprice - items_bought[key]["price"] - self.tax(lowprice)) * \
                                             items_bought[key]["amount"]
            items_bought[key]["highprofit"] = int(highprice - items_bought[key]["price"] - self.tax(highprice)) * \
                                              items_bought[key]["amount"]
            items_bought[key]["lowroi"] = round(
                ((lowprice - items_bought[key]["price"] - self.tax(lowprice)) / items_bought[key]["price"]) * 100, 2)
            items_bought[key]["highroi"] = round(
                ((highprice - items_bought[key]["price"] - self.tax(highprice)) / items_bought[key]["price"]) * 100, 2)

            lowprofit += items_bought[key]["lowprofit"]
            highprofit += items_bought[key]["highprofit"]
            items_bought_msg += f"{items_bought[key]['name']}: {items_bought[key]['lowprofit']:,} | {items_bought[key]['highprofit']:,} | {items_bought[key]['lowroi']}%-{items_bought[key]['highroi']}%\n"

        return await ctx.send(f"worst case: {lowprofit:,}\nbest case: {highprofit:,}\n\n"
                              f"{items_bought_msg}\n"
                              f"{items_sold_msg}")

    def tax(self, price):
        tax = price * 0.01
        if tax > 5_000_000:
            tax = 5_000_000

        return tax

    # async def cry_loop(self):
    #     await self.bot.wait_until_ready()
    #     while self is self.bot.get_cog('Runescape'):
    #         await run_half_hourly_task()

    async def collect_cry(self):
        pass


async def setup(bot):
    await bot.add_cog(Getracker(bot))
