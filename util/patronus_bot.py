import logging
import os
import traceback
from discord.ext.commands import Bot
from config.settings import Settings


# Returns a list of strings to attempt to load as cogs
def get_potential_cogs():
    cogs = []
    # Loop through the cogs directory
    for filename in os.listdir('./cogs'):
        # If it isn't a py file skip it
        if not filename.endswith('.py'):
            continue

        # Extract the filename without the .py
        cogs.append(f'cogs.{filename[:-3]}')

    return cogs


class PatronusBot(Bot):
    SETTINGS = Settings()

    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)

    async def setup_hook(self):
        # Load all extensions
        for cog in get_potential_cogs():
            try:
                await self.load_extension(cog)
                logging.info(f"Successfully loaded the {cog} extension!")
            except Exception as e:
                logging.error(f"Failed to load {cog} extension due to the following error!\n{e}")
                logging.error(f"{traceback.format_exc()}")

    @property
    def settings(self):
        return self.SETTINGS
