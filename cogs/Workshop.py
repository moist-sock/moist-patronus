from discord import *
from discord.ext import commands


class Workshop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.guild_only()
    async def testy(self, ctx):
        pins = await self.bot.get_channel(1212472090741973022).pins()
        print(pins[0].attachments[0].url)

    @commands.command(aliases=["embed"], hidden=True)
    async def test_embed(self, ctx):
        url="https://stackoverflow.com/questions/65133049/discord-py-links-in-embeds"
        embed_msg = Embed(title='test',
                          url=url)
        embed_msg.set_footer(text="[Click here for more](https://www.youtube.com/)")

        await ctx.send(embed=embed_msg)




async def setup(bot):
    await bot.add_cog(Workshop(bot))
