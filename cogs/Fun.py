import logging
import os

from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            # message = str(ctx.message.content).lower()
            return
        raise error

    # @commands.Cog.listener()
    # async def on_voice_state_update(self, member, before, after):
    #     target_channel_id = 909384524050337807
    #
    #     if member.id == self.bot.settings.sarah_id and after.channel and after.channel.id == target_channel_id and not self.bot.settings.sarah_id in voice_channel.:
    #         await self.bot.get_user(self.bot.settings.moist_id).send(
    #             "Baby is waiting for you in call")
    #         await self.bot.get_user(self.bot.settings.sarah_id).send(
    #             "Hello I am letting baby know that you joined call")


async def setup(bot):
    await bot.add_cog(Fun(bot))
