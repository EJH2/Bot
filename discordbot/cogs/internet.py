"""
Internet commands.
"""

from random import randint

import aiohttp
import discord
import pyowm
from bs4 import BeautifulSoup as BSoup
from discord.ext import commands

from discordbot.bot import DiscordBot
from discordbot.consts import bot_config


# noinspection PyUnboundLocalVariable
class Internet:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.command()
    async def rip(self, ctx, user: discord.User = None):
        """
        RIP.
        """
        if user is not None:
            user = user.display_name
        else:
            user = ctx.message.author.display_name
        await ctx.send("<http://ripme.xyz/{}>".format(user.replace(" ", "%20")))

    @commands.command()
    async def robohash(self, ctx, user: discord.User = None):
        """
        Robot pics.
        """
        if user is not None:
            user = user.display_name
        else:
            user = ctx.message.author.display_name
        await ctx.send("https://robohash.org/{}.png".format(user.replace(" ", "%20")))

    @commands.command()
    async def xkcd(self, ctx, query=""):
        """Queries a random XKCD comic.

        Do `^xkcd <number from 1-1662>` to pick a specific comic."""
        if not query:
            i = randint(1, 1662)
            url = "https://xkcd.com/{}/".format(i)
        elif query.isdigit() and 1 <= int(query) <= 1796:
            url = "https://xkcd.com/{}/".format(query)
        elif int(query) <= 0 or int(query) >= 1796:
            await ctx.send("It has to be between 1 and 1796!")
        elif not query.isdigit():
            await ctx.send("You have to put a number!")
        else:
            await ctx.send("I don't know how you managed to do it, but you broke it.")
        with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                r = await resp.read()
        resp = BSoup(r, "html.parser")
        await ctx.send(
            ":mag:**" + resp("img")[1]["alt"] + "**\nhttp:" + resp("img")[1]["src"] + "\n" + resp("img")[1]["title"])

    @commands.command()
    async def weather(self, ctx, *, location):
        """
        Gives the current weather in a city.
        """
        owm = pyowm.OWM(bot_config["bot"]["OWMKey"])
        observation = owm.weather_at_place(location)
        w = observation.get_weather()
        obs = w.get_detailed_status()
        if obs == "clear sky":
            await ctx.send("The weather is forecast to be a clear sky :sunny:")
        elif obs == "broken clouds":
            await ctx.send("The weather is forecast to be broken clouds :cloud:")
        else:
            await ctx.send("The weather is forecast to be " + "".join(map(str, obs)) + ".")


def setup(bot: DiscordBot):
    bot.add_cog(Internet(bot))
