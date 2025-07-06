import asyncio
import datetime
import json
import discord

import textdistance
from discord import Embed, app_commands
from discord.ext import commands

from util.async_request import request
from util.store_test_json import store_test
from util.time_functions import time_ago, run_half_hourly_task, run_daily_task
from pprint import pprint
import re


class FakeChoice:
    def __init__(self):
        self.name = "Bought"


def ge_tracker_url_gen(item):
    # Use regular expression to replace anything within parentheses
    item = re.sub(r'\((.*?)\)', r'-\1', item).lower()

    # Replace spaces and single quotes with hyphens
    item = item.replace(" ", "-").replace("'", "-").replace("/", "-").replace("--", "-")

    return f"https://www.ge-tracker.com/item/{item}"


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

        updated_item_dict = {}
        id_to_item = {}
        for item in list_of_items:
            updated_item_dict[item["name"]] = {"examine": item.get("examine", None),
                                       "id": item.get("id", None),
                                       "members": item.get("members", None),
                                       "lowalch": item.get("lowalch", None),
                                       "limit": item.get("limit", None),
                                       "value": item.get("value", None),
                                       "highalch": item.get("highalch", None),
                                       "icon": item.get("icon", None)}
            id_to_item[item.get("id", "fart")] = item.get("name", "poop")

        if updated_item_dict == self.items:
            return

        all_items = set(list(updated_item_dict.keys()) + list(self.items.keys()))

        added_items = []
        removed_items = []
        changed_items = {}

        for item in all_items:
            if item in updated_item_dict and item not in self.items:
                added_items.append(item)
                continue

            if item not in updated_item_dict and item in self.items:
                removed_items.append(item)
                continue

            if self.items[item] != updated_item_dict[item]:
                different_keys = {}
                for key in self.items[item].keys():
                    if self.items[item][key] != updated_item_dict[item][key]:
                        different_keys[key] = (self.items[item][key], updated_item_dict[item][key])

                changed_items[item] = different_keys

        msg = ""
        if added_items:
            msg += f"These items were added to runescape {', '.join(added_items)}\n"

        if removed_items:
            msg += f"These items were removed from runescape {', '.join(removed_items)}\n"

        if changed_items:
            msg += f"The following items were changed:\n"

            for item, change_dict in changed_items.items():
                msg += f"\n-- {item}\n"

                for change, before_after in change_dict.items():
                    msg += f"-- {change}: {before_after[0]} -> {before_after[1]}\n"


        try:
            await self.bot.get_user(self.bot.settings.moist_id).send(msg)

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
                await self.bot.get_user(self.bot.settings.moist_id).send(short_msg)

        self.items = updated_item_dict
        self.items_id = id_to_item

        with open("storage/osrs_items.json", "w") as f:
            json.dump(updated_item_dict, f, indent=2)

        with open("storage/osrs_item_id_dict.json", "w") as f:
            json.dump(id_to_item, f, indent=2)

    @commands.command()
    async def changes(self, ctx):
        await ctx.send("you got it boss")
        await self.update_items()

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

        url = ge_tracker_url_gen(item_name)
        embed_msg = Embed(title=item_name,
                          url=url)

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

            tax = high_price * 0.02

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

    async def cry(self, investment_dict):
        items_sold = investment_dict["items_sold"]
        items_bought = investment_dict["items_bought"]

        status, items_prices = await self.all_item_price_with_most_recent_transaction()

        if status != 200:
            print(f"error in cry, {status}")
            return

        items_prices = items_prices["data"]

        lowprofit = 0
        highprofit = 0
        items_sold_msg = ""
        items_bought_msg = ""
        for key in items_sold.keys():
            items_sold[key]["currentlow"] = items_prices[str(items_sold[key]["id"])]["low"]
            items_sold[key]["currenthigh"] = items_prices[str(items_sold[key]["id"])]["high"]
            items_sold[key]["highprofit"] = items_sold[key]["price"] - items_sold[key]["currentlow"]
            items_sold[key]["lowprofit"] = items_sold[key]["price"] - items_sold[key]["currenthigh"]

            lowprofit += items_sold[key]["lowprofit"] * items_sold[key]["amount"]
            highprofit += items_sold[key]["highprofit"] * items_sold[key]["amount"]

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

        return f"worst case: {lowprofit:,}\nbest case: {highprofit:,}\n\n{items_bought_msg}\n{items_sold_msg}"

    @app_commands.command(name="invest", description="track investments :D")
    @app_commands.describe(initial='Options to choose from')
    @app_commands.choices(initial=[
        discord.app_commands.Choice(name='View', value=1),
        discord.app_commands.Choice(name='Add', value=2),
        discord.app_commands.Choice(name='Remove', value=3)
    ])
    @app_commands.choices(transaction=[
        discord.app_commands.Choice(name="Bought", value=1),
        discord.app_commands.Choice(name="Sold", value=2)
    ])
    @app_commands.guild_only()
    async def invest_slash(self, interaction: discord.Interaction, initial: discord.app_commands.Choice[int],
                           investment: str,
                           item: str = None,
                           amount: str = None,
                           price: str = None,
                           transaction: discord.app_commands.Choice[int] = None):

        if transaction is None:
            transaction = FakeChoice()

        if item is not None:
            item = await self.get_real_item(item)

        try:
            with open("storage/investments.json", "r") as f:
                investment_dict = json.load(f)

        except FileNotFoundError:
            investment_dict = {}

        try:
            real_investment = investment_dict[investment]

        except KeyError:
            if initial.name in ["View", "Remove"]:
                return await interaction.response.send_message(f"No tracked investment with the name `{investment}`")

            real_investment = {}

        match initial.name:

            case "View":
                msg = await self.cry(real_investment)
                return await interaction.response.send_message(msg)
            case "Add":
                if item is None or amount is None or price is None:
                    return interaction.response.send_message(
                        f"If youre gonna add youre gonna need to give me item, amount and price")
                real_investment = await self.add_investment(real_investment, item, amount, price, transaction.name)
                await self.save_investment(investment_dict, real_investment, investment)
                return await interaction.response.send_message(
                    f"Sucessfully added {transaction.name} {item} to investment {investment}")

            case "Remove":
                try:
                    real_investment = await self.remove_investment(real_investment, item, transaction.name)

                except KeyError:
                    return await interaction.response.send_message(
                        f"Could not remove {item} from the {transaction.name} portion of the investment file {investment}")

                await self.save_investment(investment_dict, real_investment, investment)
                return await interaction.response.send_message(
                    f"Successfully removed {item} from the {transaction.name} portion of the investment file {investment}")

    async def add_investment(self, real_investment, item, amount, price, buy_or_sell):
        # items_sold = {}
        # items_bought = {"tbow": {"price": 1_607_000_000,
        #                          "amount": 7,
        #                          "name": "Twisted bow",
        #                         "id": 20997}
        #                 }

        items_bought = real_investment.get("items_bought", {})
        items_sold = real_investment.get("items_sold", {})

        price = price.replace(",", "")
        amount = amount.replace(",", "")

        if buy_or_sell == "Bought":
            items_bought[item] = {"price": int(price),
                                       "amount": int(amount),
                                       "name": item,
                                       "id": self.items[item]["id"]
                                  }
        else:
            items_sold[item] = {"price": int(price),
                                     "amount": int(amount),
                                     "name": item,
                                     "id": self.items[item]["id"]
                                }
        real_investment["items_bought"] = items_bought
        real_investment["items_sold"] = items_sold
        return real_investment

    async def remove_investment(self, real_investment, item, bought_or_sold):
        item = await self.get_real_item(item)
        if bought_or_sold == "Bought":
            del real_investment["items_bought"][item]
        elif bought_or_sold == "Sold":
            del real_investment["items_sold"][item]
        else:
            raise KeyError

    async def save_investment(self, whole_investment_dict, lil_investment_dict, name_of_investment):
        whole_investment_dict[name_of_investment] = lil_investment_dict
        with open("storage/investments.json", "w") as f:
            json.dump(whole_investment_dict, f, indent=2)

    async def get_real_item(self, item):
        distances = []
        for real_item in self.items:
            distances.append([real_item, textdistance.Levenshtein()(real_item.lower(), item)])

        return sorted(distances, key=lambda x: x[1])[0][0]

    def tax(self, price):
        tax = price * 0.02
        if tax > 5_000_000:
            tax = 5_000_000

        return tax


async def setup(bot):
    await bot.add_cog(Getracker(bot))
