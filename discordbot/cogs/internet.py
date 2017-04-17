"""
Internet commands.
"""
import aiohttp
import datetime
import discord
import geocoder
import io
import xkcd
from discord.ext import commands

from discordbot.bot import DiscordBot
from discordbot.consts import bot_config
from discordbot.cogs.utils import checks, util


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
        url = "https://robohash.org/{}.png".format(user.replace(" ", "%20"))
        file = await util.get_file(url)
        await ctx.send(file=discord.File(fp=io.BytesIO(file), filename="robot.png"))

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
        lat, lng = g.latlng
        crippling_depression = bot_config["bot"]["OWMKey"]
        you_made_me_do_this_forcastio = "https://api.darksky.net/forecast/{}/{},{}".format(crippling_depression,
                                                                                           lat, lng)
        print(you_made_me_do_this_forcastio)
        with aiohttp.ClientSession() as sess:
            async with sess.get(you_made_me_do_this_forcastio) as how_could_you:
                assert isinstance(how_could_you, aiohttp.ClientResponse)
                oh_the_pain = await how_could_you.json()
        print(oh_the_pain)
        today = oh_the_pain["daily"]["data"][0]
        print(today)
        await ctx.send("Location: {}, {}\n"
                       "Sunrise Time: {}\n"
                       "Sunset Time: {}\n"
                       "Weather: {}\n"
                       "Temperature Min (Apparent): {} Degrees ({} Degrees)\n"
                       "Temperature Max (Apparent): {} Degrees ({} Degrees)\n".format(g.city, g.state, datetime.
                                                                                      datetime.fromtimestamp(
                                                                                        int(today["sunriseTime"])).
                                                                                      strftime('%Y-%m-%d %H:%M:%S'),
                                                                                      datetime.datetime.fromtimestamp(
                                                                                          int(today[
                                                                                                  "sunsetTime"])).
                                                                                      strftime(
                                                                                          '%Y-%m-%d %H:%M:%S'),
                                                                                      today["summary"],
                                                                                      today["temperatureMin"],
                                                                                      today["apparentTemperatureMin"],
                                                                                      today["temperatureMax"],
                                                                                      today["apparentTemperatureMax"]))


def setup(bot: DiscordBot):
    bot.add_cog(Internet(bot))
