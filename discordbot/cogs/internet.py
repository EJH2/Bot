"""
Internet commands.
"""

import os
from random import randint

import aiohttp
import discord
import pyowm
from bs4 import BeautifulSoup as BSoup
from discord.ext import commands

from discordbot.bot import DiscordBot
from discordbot.cogs.utils import util
from discordbot.consts import bot_config


# noinspection PyUnboundLocalVariable
class Internet:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def penguin(self, ctx):
        """
        Penguins!
        """
        url = "http://penguin.wtf/"
        i = randint(0, 100)
        path = "discordbot/cogs/utils/files/penguin{}.png".format(i)
        with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                r = await resp.read()
        await util.download(r.decode("utf-8"), path)
        await self.bot.upload(path)
        os.remove(path)

    @commands.command()
    async def rip(self, user: discord.User):
        """
        RIP.
        """
        user = user.display_name
        await self.bot.say("<http://ripme.xyz/{}>".format(user.replace(" ", "%20")))

    @commands.command()
    async def robohash(self, user: discord.User):
        """
        Robot pics.
        """
        user = user.display_name
        await self.bot.say("https://robohash.org/{}.png".format(user.replace(" ", "%20")))

    @commands.command()
    async def xkcd(self, query=""):
        """Queries a random XKCD comic.

        Do `^xkcd <number from 1-1662>` to pick a specific comic."""
        if not query:
            i = randint(1, 1662)
            url = "https://xkcd.com/{}/".format(i)
        elif query.isdigit() and 1 <= int(query) <= 1662:
            url = "https://xkcd.com/{}/".format(query)
        elif int(query) <= 0 or int(query) >= 1663:
            await self.bot.say("It has to be between 1 and 1662!")
        elif not query.isdigit():
            await self.bot.say("You have to put a number!")
        else:
            await self.bot.say("I don't know how you managed to do it, but you borked it.")
        with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                r = await resp.read()
        resp = BSoup(r, "html.parser")
        await self.bot.say(
            ":mag:**" + resp("img")[1]["alt"] + "**\nhttp:" + resp("img")[1]["src"] + "\n" + resp("img")[1]["title"])

    @commands.command()
    async def weather(self, *, location):
        """
        Gives the current weather in a city.
        """
        owm = pyowm.OWM(bot_config["bot"]["OWMKey"])
        observation = owm.weather_at_place(location)
        w = observation.get_weather()
        obs = w.get_detailed_status()
        if obs == "clear sky":
            await self.bot.say("The weather is forecast to be a clear sky :sunny:")
        elif obs == "broken clouds":
            await self.bot.say("The weather is forecast to be broken clouds :cloud:")
        else:
            await self.bot.say("The weather is forecast to be " + "".join(map(str, obs)) + ".")


def setup(bot: DiscordBot):
    bot.add_cog(Internet(bot))
