import discord
from util import settings
from discord.ext import commands

logger = settings.logging.getLogger("bot")


def run():
    with open("config/chickentoken.txt", "r") as f:
        token = f.read()
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix="!", intents=intents)
    bot.logger = logger

    @bot.event
    async def on_ready():
        logger.info(f"Logged in as {bot.user}")

        for cog in settings.COGS_DIR.glob("*.py"):
            cog = f"cogs.{cog.name[:-3]}"
            await bot.load_extension(cog)

    bot.run(token, root_logger=True)


if __name__ == "__main__":
    run()
