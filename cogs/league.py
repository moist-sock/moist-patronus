import json
import asyncio

import datetime

import discord
import textdistance
from discord import Embed

from util import async_request
from discord.ext import commands
from discord.ext.commands import Cog
from util import champs
from util.settings import moist_id

try:
    with open('storage/league.json') as f:
        league_dict = json.load(f)

    the_token = league_dict['token']

except FileNotFoundError:
    # Token is set to a string that needs some characters in it so the status code returns "403 forbidden"
    # It causes less errors this way vs an empty string
    league_dict = {'token': 'None', 'users': {}}

    with open('storage/league.json', 'w') as f:

        json.dump(league_dict, f, indent=2)

    the_token = league_dict['token']


class League(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.expired = f'I will not work until <@765451755332304927> feeds me token :('

        try:
            self.token = the_token
        except NameError:
            self.token = None

        self.champion_info = champs.CHAMP_INFO

    def _check_if_not_moist(self, ctx):
        """Checks if the moist is the one that used the command."""
        return ctx.author.id != moist_id and ctx.author.id != 765451755332304927

    @commands.command()
    async def token(self, ctx, *args):
        """Command that easily allows me to update the RIOT api key"""
        if self._check_if_not_moist(ctx):
            return await ctx.send('You are not allowed to do that')

        new_api_key = args[0].strip()
        for i in range(50):
            r = await async_request.request(f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/moist s0ck',
                                            headers={"X-Riot-Token": new_api_key})

            if r[0] == 200:
                break

        if r[0] != 200:
            return await ctx.send(f'API key failed to update!\nError#: {r[0]}')

        with open('storage/league.json', 'w') as f:
            league_dict['token'] = new_api_key
            json.dump(league_dict, f, indent=2)

        self.token = new_api_key

        return await ctx.send('API key successfully updated')

    @commands.command()
    async def streak(self, ctx, *args):
        """Checks the win/loss ranked streak of an NA gamer."""
        if self._check_if_not_moist(ctx):
            return await ctx.send('You are not allowed to do that')

        emote = ''
        outcome = ''
        last_few_games = []
        summoner_name = " ".join(args)
        r = await async_request.request(f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/'
                                        f'{summoner_name}',
                                        headers={"X-Riot-Token": self.token})
        if r[0] != 200:
            if r[0] == 403:
                return await ctx.send(self.expired)

            return await ctx.send(f'No1: {r[0]}')

        summoner_puuid = r[1]['puuid']
        summoner_name = r[1]['name']
        r = await async_request.request(
            f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoner_puuid}'
            f'/ids?type=ranked&start=0&count=10',
            headers={"X-Riot-Token": self.token})

        if r[0] != 200:
            return await ctx.send(f'No2: {r[0]}')

        match_ids = r[1]

        for match_id in match_ids:
            r = await async_request.request(
                f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}',
                headers={"X-Riot-Token": self.token})

            if r[0] != 200:
                return await ctx.send(f'No3: {r[0]}')

            index = r[1]['metadata']['participants'].index(summoner_puuid)

            if not last_few_games:
                last_few_games.append(r[1]['info']['participants'][index]['win'])

            elif last_few_games[0] == r[1]['info']['participants'][index]['win']:
                last_few_games.append(r[1]['info']['participants'][index]['win'])

            else:
                break

        if last_few_games and last_few_games[0]:
            outcome = 'win'
            emote = ':)'

        elif last_few_games and not last_few_games[0]:
            outcome = 'loss'
            emote = ':('

        if outcome:
            return await ctx.send(
                f'{summoner_name} is on a {len(last_few_games)} game {outcome} streak in ranked! {emote}')

        return await ctx.send('No games of ranked found')

    @commands.command()
    async def summoner(self, ctx, *args, ff=False):
        """Adds summoner info into json so the mastery command will work."""
        summoner_name = " ".join(args).strip()
        if summoner_name is None or summoner_name == '':
            return await ctx.send("You need to type your league name silly goose!")

        r = await async_request.request(
            f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}',
            headers={"X-Riot-Token": self.token})

        status_code = r[0]
        if status_code != 200:
            if status_code == 404:
                return await ctx.send(f"The summoner name `{summoner_name}` does not exist!!")

            elif status_code == 403:
                return await ctx.send(self.expired)

            return await ctx.send(f'Error Code: {status_code}')

        summoner_name = r[1]['name']
        summoner_id = r[1]['id']

        with open('storage/league.json', 'w') as f:
            persons_id = str(ctx.author.id)
            league_dict['users'][persons_id] = {'summoner name': summoner_name, 'summoner id': summoner_id}
            json.dump(league_dict, f, indent=2)

        if ff:
            return

        return await ctx.send(f"Summoner name `{summoner_name}` successfully added as your account")

    @commands.command(name='mastery', aliases=['m', 'M', 'chest'])
    async def mastery(self, ctx, *args, ff=False):
        """Returns mastery level + chest availability for specific champion for an account."""

        champion = await self.parse_champion_input(args)
        champion_color = int(self.champion_info[champion]['COLOR'], 16)

        try:
            champion_id = champs.CHAMP_INFO[champion]['ID']

        except KeyError:
            return await ctx.send(f'Please check champion spelling: `{champion}`')

        try:
            # pycharm was giving moist annoying warnings these comments got rid of them
            # Expected type 'Union[int, slice]', got 'str' instead

            # noinspection PyTypeChecker
            summoner_name = league_dict['users'][str(ctx.author.id)]['summoner name']
            # noinspection PyTypeChecker
            summoner_id = league_dict['users'][str(ctx.author.id)]['summoner id']

        except KeyError:
            return await ctx.send(f'Please set your league account with !summoner')

        status_code, mastery_info = await self.mastery_request(summoner_id, champion_id)

        if status_code == 200:
            mastery_level = mastery_info['championLevel']
            chest_earned = mastery_info['chestGranted']
            mastery_points = mastery_info['championPoints']
            last_played = mastery_info['lastPlayTime']
            tokens_earned = mastery_info['tokensEarned']

        elif status_code == 403:
            return await ctx.send(self.expired)

        elif status_code == 404:
            mastery_level = 0
            chest_earned = 'Of course not'
            mastery_points = 0
            last_played = 0
            tokens_earned = 0

        elif status_code == 429:
            await ctx.send("Rate limit exceeded! Trying again in one minute")
            await asyncio.sleep(60)
            return await self.mastery(ctx, champion)

        elif status_code == 400 and not ff:
            await self.summoner(ctx, league_dict['users'][str(ctx.author.id)]['summoner name'], ff=True)
            return await self.mastery(ctx, champion, ff=True)

        else:
            return await ctx.send(f'Error point 1: {status_code}')

        png = champs.CHAMP_INFO[champion]['PNG']

        embed_msg = Embed(
            title=f'{champion} - {summoner_name}',
            type='rich',
            description="",
            colour=champion_color
        )

        embed_msg.set_thumbnail(url=png)
        embed_msg.add_field(name='Mastery Points', value=f"{mastery_points:,}", inline=False)  # large numbers get comma
        embed_msg.add_field(name='Mastery Level', value=mastery_level)
        embed_msg.add_field(name='Chest Earned', value=chest_earned)

        if mastery_level < 5:
            embed_msg.add_field(name='Points Until Level 5', value=f"{21600 - mastery_points:,}", inline=False)
        elif mastery_level == 5:
            embed_msg.add_field(name='Tokens needed', value=str(2 - tokens_earned), inline=False)
        elif mastery_level == 6:
            embed_msg.add_field(name='Tokens needed', value=str(3 - tokens_earned), inline=False)

        if last_played:
            embed_msg.set_footer(
                text=f"Last played {datetime.datetime.fromtimestamp(last_played / 1000).strftime('%a %b %d, %Y')}")

        else:
            embed_msg.set_footer(text=f'Last played NEVER')

        return await ctx.send(embed=embed_msg)

    @commands.command(name='ci')
    async def champion_information(self, ctx):
        if str(ctx.author.top_role) != 'Admins':
            return await ctx.send('Why do you even want this')

        return await ctx.send(content='Here you go!!', file=discord.File('storage/champion_info.json'))

    @commands.command(name='color', aliases=['colour'])
    async def color(self, ctx, *args):
        if ctx.author.id != moist_id:
            return

        champion = await self.parse_champion_input([args[0]])
        try:
            new_color = int(args[1], 16)

            if new_color > 16777215:
                return await ctx.send('Try a real color')

        except:
            return await ctx.send('Try a real color')

        png = self.champion_info[champion]['PNG']

        before_embed_msg = Embed(
            title=f'{champion}',
            type='rich',
            description="",
            colour=int(self.champion_info[champion]['COLOR'], 16)
        )

        after_embed_msg = Embed(
            title=f'{champion}',
            type='rich',
            description="",
            colour=new_color
        )
        before_embed_msg.set_thumbnail(url=png)
        after_embed_msg.set_thumbnail(url=png)
        before_embed_msg.add_field(name='Old Color', value=f"{hex(int(self.champion_info[champion]['COLOR'], 16))}")
        after_embed_msg.add_field(name='New Color', value=f'{hex(new_color)}')

        try:
            await ctx.send(embed=before_embed_msg)
            await ctx.send(embed=after_embed_msg)
            await ctx.send(f'would you like to change the color for {champion} to {hex(int(new_color))}?\n'
                           f'`y` or `n`')
            msg = await self.bot.wait_for('message',
                                          check=lambda message: message.author == ctx.author and
                                          message.channel.id == ctx.channel.id, timeout=10)

        except asyncio.exceptions.TimeoutError:
            return await ctx.send('TOO SLOW')

        if msg.content == 'y':
            return await ctx.send('Color has been changed')

        else:
            return await ctx.send('Color has not been changed')

    async def id(self, summoner_name):
        r = await async_request.request(
            f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}',
            headers={"X-Riot-Token": self.token})

        status_code = r[0]
        if status_code != 200:
            return status_code, None, None

        return status_code, r[1]['id'], r[1]['name']

    async def mastery_request(self, summoner_id, champion_id):
        r = await async_request.request(
            f'https://na1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/'
            f'{summoner_id}/by-champion/{champion_id}',
            headers={"X-Riot-Token": self.token})

        status_code = r[0]
        if status_code != 200:
            return status_code, None

        return status_code, r[1]

    async def parse_champion_input(self, raw_input):
        # Parses input
        # example input: !mastery urgot
        champion = ' '.join(raw_input).title()

        distances = []
        for real_champion in champs.CHAMP_INFO:

            if 'ALIAS' in champs.CHAMP_INFO[real_champion]:
                champion_alias = champs.CHAMP_INFO[real_champion]['ALIAS']

                for alias in champion_alias:
                    if alias in champion:
                        return real_champion

            distances.append([real_champion, textdistance.Levenshtein()(real_champion, champion)])

        # try to remember what this does JOSE - past jose
        return sorted(distances, key=lambda x: x[1])[0][0]


async def setup(bot):
    await bot.add_cog(League(bot))
