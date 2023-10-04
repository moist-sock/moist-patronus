from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            # message = str(ctx.message.content).lower()
            return


async def setup(bot):
    await bot.add_cog(Fun(bot))
