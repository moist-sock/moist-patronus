from discord import Embed
from discord.ext import commands


class Workshop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.guild_only()
    async def testy(self, ctx):
        print(ctx.message.content)
        await ctx.send("yes ysou testy")

    @commands.command(aliases=["embed"], hidden=True)
    async def test_embed(self, ctx, url):
        embed_msg = Embed(title='test')
        embed_msg.set_thumbnail(url=url)
        embed_msg.set_image(url=url)
        await ctx.send(embed=embed_msg)


async def setup(bot):
    await bot.add_cog(Workshop(bot))
