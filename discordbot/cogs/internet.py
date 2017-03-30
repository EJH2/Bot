"""
Internet commands.
"""

import discord
import geocoder
import pyowm
import xkcd
from discord.ext import commands

from discordbot.bot import DiscordBot
from discordbot.consts import bot_config
from discordbot.cogs.utils import checks


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
    @commands.check(checks.needs_embed)
    async def xkcd(self, ctx, query: int = None):
        """Queries a random XKCD comic.

        Do `^xkcd <number>` to pick a specific comic.
        Alternatively, do `^xkcd latest` to get the latest comic!"""
        if query == 404:
            em = discord.Embed(color=discord.Color.red())
            em.title = "\N{CROSS MARK} Error"
            em.description = "Error 404: Comic "
            await ctx.send(embed=em)
            return
        latest_comic = xkcd.getLatestComicNum()
        if query:
            query_req = 1 <= int(query) <= int(latest_comic)
            if query_req:
                comic = xkcd.getComic(query)
            else:
                em = discord.Embed(color=discord.Color.red())
                em.title = "\N{CROSS MARK} Error"
                em.description = "It has to be between 1 and {}!".format(str(latest_comic))
                await ctx.send(embed=em)
                return
        else:
            comic = xkcd.getRandomComic()
        embed = discord.Embed(title=comic.title, colour=discord.Colour(0x586024), url=comic.getExplanation(),
                              description=comic.altText, timestamp=ctx.message.created_at)

        embed.set_image(url=comic.imageLink)
        embed.set_author(name="XKCD #{}".format(comic.number), url=comic.link,
                         icon_url="https://xkcd.com/s/919f27.ico")

        await ctx.send(embed=embed)

    @commands.command()
    async def weather(self, ctx, *, location):
        """
        Gives the current weather in a city.
        """
        g = geocoder.google(location)
        owm = pyowm.OWM(bot_config["bot"]["OWMKey"])
        observation = owm.weather_at_place(location)
        w = observation.get_weather()
        obs = w.get_detailed_status()
        if obs == "clear sky":
            await ctx.send("The weather is forecast to be a clear sky :sunny: in {}, {}".format(g.city, g.state))
        elif obs == "broken clouds":
            await ctx.send("The weather is forecast to be broken clouds :cloud: in {}, {}".format(g.city, g.state))
        else:
            await ctx.send("The weather is forecast to be " + "".join(map(str, obs)) + " in {}, {}".format(g.city,
                                                                                                           g.state))


def setup(bot: DiscordBot):
    bot.add_cog(Internet(bot))
