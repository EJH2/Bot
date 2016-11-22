"""
Salty commands, require the bot to have the role "Salty"
"""
import aiohttp
import discord
from bs4 import BeautifulSoup as Soup
from discord.ext import commands

from discordbot.bot import DiscordBot
from discordbot.cogs.utils import checks


class Salty:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.command()
    @checks.role("salty")
    async def insult(self, user: discord.User = None):
        """Insults a user."""
        url = "http://www.insultgenerator.org/"
        with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                r = await resp.read()
        resp = Soup(r, 'html.parser')
        if user is not None:
            pre = user.name + ": "
        else:
            pre = ""
        await self.bot.say(pre + resp.find('div', {'class': 'wrap'}).text.strip("\n"))

    @commands.command()
    async def urband(self, *, query: str):
        """
        Finds a phrase in the Urban Dictionary.
        """
        url = "http://api.urbandictionary.com/v0/define?term={}".format(query.replace(" ", "%20"))
        with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                r = await resp.json()
        try:
            await self.bot.say(r['list'][0]['definition'])
        except AttributeError:
            await self.bot.say(
                "Either the page doesn't exist, or you typed it in wrong. Either way, please try again.")


def setup(bot: DiscordBot):
    bot.add_cog(Salty(bot))
