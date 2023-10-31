from discord.ext import commands
from util.async_request import request
from util.store_test_json import store_test
import textdistance


class Thea(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raw_food = ["Meat",
                         "Bird",
                         "Fish",
                         "Vegetable",
                         "Mushroom",
                         "Fruit",
                         "Exotic",
                         "Seaweed",
                         "Grain",
                         "Nuts",
                         "Herbs"]
        self.crafted_food = {
            "Jerky1": {
                "ingredient1": "Meat",
                "ingredient2": "Meat",
                "method": "Cooked"
            },
            "Jerky2": {
                "ingredient1": "Meat",
                "ingredient2": "Bird",
                "method": "Cooked"
            },
            "Meat Stew1": {
                "ingredient1": "Meat",
                "ingredient2": "Herbs",
                "method": "Cooked"
            },
            "Pulpety1": {
                "ingredient1": "Meat",
                "ingredient2": "Seaweed",
                "method": "Cooked"
            },
            "Rabbit Stew1": {
                "ingredient1": "Meat",
                "ingredient2": "Fruit",
                "method": "Cooked"
            },
            "Rabbit Stew2": {
                "ingredient1": "Meat",
                "ingredient2": "Exotic",
                "method": "Cooked"
            },
            "Cooked Bird1": {
                "ingredient1": "Bird",
                "ingredient2": "Meat",
                "method": "Cooked"
            },
            "Cooked Bird2": {
                "ingredient1": "Bird",
                "ingredient2": "Bird",
                "method": "Cooked"
            },
            "Meat Stew2": {
                "ingredient1": "Bird",
                "ingredient2": "Herbs",
                "method": "Cooked"
            },
            "Meat Stew3": {
                "ingredient1": "Bird",
                "ingredient2": "Seaweed",
                "method": "Cooked"
            },
            "Duck in Plum Sauce1": {
                "ingredient1": "Bird",
                "ingredient2": "Fruit",
                "method": "Cooked"
            },
            "Duck in Plum Sauce2": {
                "ingredient1": "Bird",
                "ingredient2": "Exotic",
                "method": "Cooked"
            },
            "Bigos1": {
                "ingredient1": "Vegetable",
                "ingredient2": "Meat",
                "method": "Cooked"
            },
            "Bigos2": {
                "ingredient1": "Vegetable",
                "ingredient2": "Bird",
                "method": "Cooked"
            },
            "Cooked Greens1": {
                "ingredient1": "Vegetable",
                "ingredient2": "Herbs",
                "method": "Cooked"
            },
            "Cooked Greens2": {
                "ingredient1": "Vegetable",
                "ingredient2": "Seaweed",
                "method": "Cooked"
            },
            "Leczo1": {
                "ingredient1": "Vegetable",
                "ingredient2": "Fruit",
                "method": "Cooked"
            },
            "Leczo2": {
                "ingredient1": "Vegetable",
                "ingredient2": "Exotic",
                "method": "Cooked"
            },
            "Bigos3": {
                "ingredient1": "Mushroom",
                "ingredient2": "Meat",
                "method": "Cooked"
            },
            "Bigos4": {
                "ingredient1": "Mushroom",
                "ingredient2": "Bird",
                "method": "Cooked"
            },
            "Mushroom Soup1": {
                "ingredient1": "Mushroom",
                "ingredient2": "Herbs",
                "method": "Cooked"
            },
            "Mushroom Soup2": {
                "ingredient1": "Mushroom",
                "ingredient2": "Seaweed",
                "method": "Cooked"
            },
            "Mushroom Soup3": {
                "ingredient1": "Mushroom",
                "ingredient2": "Fruit",
                "method": "Cooked"
            },
            "Mushroom Soup4": {
                "ingredient1": "Mushroom",
                "ingredient2": "Exotic",
                "method": "Cooked"
            },
            "Fish Gulash1": {
                "ingredient1": "Fish",
                "ingredient2": "Meat",
                "method": "Cooked"
            },
            "Fish Gulash2": {
                "ingredient1": "Fish",
                "ingredient2": "Bird",
                "method": "Cooked"
            },
            "Cooked Fish1": {
                "ingredient1": "Fish",
                "ingredient2": "Herbs",
                "method": "Cooked"
            },
            "Fish Tartare1": {
                "ingredient1": "Fish",
                "ingredient2": "Seaweed",
                "method": "Cooked"
            },
            "Fish Salad1": {
                "ingredient1": "Fish",
                "ingredient2": "Fruit",
                "method": "Cooked"
            },
            "Fish Salad2": {
                "ingredient1": "Fish",
                "ingredient2": "Exotic",
                "method": "Cooked"
            },
            "Pierogi1": {
                "ingredient1": "Meat",
                "ingredient2": "Grain",
                "method": "Roasted"
            },
            "Pierogi2": {
                "ingredient1": "Meat",
                "ingredient2": "Nuts",
                "method": "Roasted"
            },
            "Meat Roast1": {
                "ingredient1": "Meat",
                "ingredient2": "Herbs",
                "method": "Roasted"
            },
            "Sausages1": {
                "ingredient1": "Meat",
                "ingredient2": "Vegetable",
                "method": "Roasted"
            },
            "Meat Kebabs1": {
                "ingredient1": "Meat",
                "ingredient2": "Mushroom",
                "method": "Roasted"
            },
            "Chicken Pie1": {
                "ingredient1": "Bird",
                "ingredient2": "Grain",
                "method": "Roasted"
            },
            "Chicken Pie2": {
                "ingredient1": "Bird",
                "ingredient2": "Nuts",
                "method": "Roasted"
            },
            "Bird Roast1": {
                "ingredient1": "Bird",
                "ingredient2": "Herbs",
                "method": "Roasted"
            },
            "Bird Casserole1": {
                "ingredient1": "Bird",
                "ingredient2": "Vegetable",
                "method": "Roasted"
            },
            "Bird Shashlik1": {
                "ingredient1": "Bird",
                "ingredient2": "Mushroom",
                "method": "Roasted"
            },
            "Fish Pie1": {
                "ingredient1": "Fish",
                "ingredient2": "Grain",
                "method": "Roasted"
            },
            "Fish Pie2": {
                "ingredient1": "Fish",
                "ingredient2": "Nuts",
                "method": "Roasted"
            },
            "Roasted Fish1": {
                "ingredient1": "Fish",
                "ingredient2": "Herbs",
                "method": "Roasted"
            },
            "Fish Casserole1": {
                "ingredient1": "Fish",
                "ingredient2": "Vegetable",
                "method": "Roasted"
            },
            "Grilled Fish and Mushrooms1": {
                "ingredient1": "Fish",
                "ingredient2": "Mushroom",
                "method": "Roasted"
            },
            "Bread1": {
                "ingredient1": "Grain",
                "ingredient2": "Grain",
                "method": "Baked"
            },
            "Fruit Pie1": {
                "ingredient1": "Grain",
                "ingredient2": "Nuts",
                "method": "Baked"
            },
            "Fruit Pie2": {
                "ingredient1": "Grain",
                "ingredient2": "Fruit",
                "method": "Baked"
            },
            "Fruit Pie3": {
                "ingredient1": "Grain",
                "ingredient2": "Exotic",
                "method": "Baked"
            },
            "Granary Roll1": {
                "ingredient1": "Nuts",
                "ingredient2": "Grain",
                "method": "Baked"
            },
            "Porrige1": {
                "ingredient1": "Nuts",
                "ingredient2": "Nuts",
                "method": "Baked"
            },
            "Porrige2": {
                "ingredient1": "Nuts",
                "ingredient2": "Fruit",
                "method": "Baked"
            },
            "Porrige3": {
                "ingredient1": "Nuts",
                "ingredient2": "Exotic",
                "method": "Baked"
            },
            "Seaweed Pie1": {
                "ingredient1": "Seaweed",
                "ingredient2": "Grain",
                "method": "Baked"
            },
            "Seaweed Cookies1": {
                "ingredient1": "Seaweed",
                "ingredient2": "Nuts",
                "method": "Baked"
            },
            "Seaweed Fruitcake1": {
                "ingredient1": "Seaweed",
                "ingredient2": "Fruit",
                "method": "Baked"
            },
            "Seaweed Cookies2": {
                "ingredient1": "Seaweed",
                "ingredient2": "Exotic",
                "method": "Baked"
            }
        }

    @commands.command()
    async def thea(self, ctx, *foods):
        clean_foods = []
        for food in foods:
            clean_foods.append(self.parse_food(food))

        legal_food = []
        for thing in self.crafted_food:
            ing1 = self.crafted_food[thing]['ingredient1']
            ing2 = self.crafted_food[thing]['ingredient2']
            if ing1 in clean_foods and ing2 in clean_foods:
                legal_food.append(f"{self.crafted_food[thing]['method']}: {ing1} and {ing2} - {thing}")

        total_food = len(clean_foods) + len(legal_food)
        if "Herbs" in clean_foods:
            total_food -= 1
        msg = f"You can have {total_food} food with those ingredients\n"
        msg += "\n".join(legal_food)

        await ctx.send(msg)

    def parse_food(self, food):
        distances = []
        for real_food in self.raw_food:
            distances.append([real_food, textdistance.Levenshtein()(real_food, food)])

        return sorted(distances, key=lambda x: x[1])[0][0]


async def setup(bot):
    await bot.add_cog(Thea(bot))
