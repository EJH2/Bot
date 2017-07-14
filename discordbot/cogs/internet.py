"""
Internet commands.
"""
import datetime
import functools
import io

import aiohttp
import astral
import darksky
import discord
import geocoder
import pytz
import wikipedia
import wikipedia.exceptions
import xkcd
from discord.ext import commands

from discordbot.bot import DiscordBot
from discordbot.cogs.utils import checks, util
from discordbot.consts import bot_config


# noinspection PyUnboundLocalVariable
def get_moon_phase(date):
    """
    Get Moon Phase.
    """
    ast = astral.Astral()
    phase_int = int(ast.moon_phase(date))
    if phase_int == 0:
        phase = "New moon"
    elif phase_int <= 7:
        phase = "Waxing crescent"
    elif phase_int == 7:
        phase = "First quarter"
    elif 7 < phase_int < 14:
        phase = "Waxing gibbous"
    elif phase_int == 14:
        phase = "Full moon"
    elif 14 < phase_int < 21:
        phase = "Waning gibbous"
    elif phase_int == 21:
        phase = "Last quarter"
    elif 21 < phase_int < 28:
        phase = "Waning crescent"
    else:
        phase = "New moon"
    return phase


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
            user = ctx.author.display_name
        await ctx.send("<http://ripme.xyz/{}>".format(user.replace(" ", "%20")))

    @commands.command()
    async def robohash(self, ctx, user: discord.User = None):
        """
        Robot pics.
        """
        if user is not None:
            user = user.display_name
        else:
            user = ctx.author.display_name
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
            em.description = "Error 404: Comic Not Found"
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
        key = bot_config["bot"].get("WeatherKey", None)
        if not key:
            return
        g = geocoder.google(location)
        if not g.latlng:
            return await ctx.send("Sorry, I couldn't find that place!")
        lat, lng = g.latlng
        loc = g.address
        args = functools.partial(darksky.forecast, key, lat, lng, units="auto")
        forc = await ctx.bot.loop.run_in_executor(None, args)
        with forc as forecast:
            today = forecast.daily.data[0]
            now = forecast.currently
            now_time = datetime.datetime.fromtimestamp(int(now.time), tz=pytz.timezone(forecast.timezone)
                                                       ).strftime('%H:%M:%S')
            phase = get_moon_phase(datetime.datetime.fromtimestamp(int(today.time), tz=pytz.timezone(
                forecast.timezone)))
            try:
                _alerts = []
                alerts = "None"
                for i in forecast.alerts:
                    i.expires = datetime.datetime.fromtimestamp(int(i.expires)).strftime("%A, %B %d at %H:%M:%S")
                    i.regions = ", ".join(i.regions)
                    i.severity = i.severity.title()
                    _alerts += ["[{}: {} in {}]({} 'Click for Full Description'): Expires on {}\n".format(
                        str(i.severity), str(i.title), str(i.regions), str(i.uri), str(i.expires))]
                    alerts = "\n".join(_alerts)
            except AttributeError:
                alerts = "None"
            unit = forecast.flags.units
            if unit != "us":
                temp = "C"
                if unit == "si":
                    wind = "Meters/Second"
                elif unit == "ca":
                    wind = "Kilometers/Hour"
                elif unit == "uk2":
                    wind = "Miles/Hour"
                else:
                    wind = "Miles/Hour"
            else:
                temp = "F"
                wind = "Miles/Hour"
            em = discord.Embed(title="Weather in {} at {}".format(loc, now_time),
                               description="Here is today's forecast:")
            em.set_thumbnail(url="https://discord.lol-sa.me/files/weather/{}.png".format(today.icon) if
            today.icon in ["clear-day", "clear-night", "rain", "snow", "sleet", "wind", "fog",
                           "cloudy", "partly-cloudy-day", "partly-cloudy-night"] else None)
            em.set_footer(text="Powered by Dark Sky", icon_url="https://discord.lol-sa.me/files/weather/darksky.png")
            try:
                sunrise, sunset = (datetime.datetime.fromtimestamp(int(today.sunriseTime), tz=pytz.timezone(
                    forecast.timezone)).strftime('%H:%M:%S'),
                                   datetime.datetime.fromtimestamp(int(today.sunsetTime),
                                                                   tz=pytz.timezone(forecast.timezone)).strftime
                                   ('%H:%M:%S'))
            except AttributeError:
                sunrise, sunset = "None", "None"
            em.add_field(name="Today's Weather", value=today.summary)
            em.add_field(name="Temp Range", value="{} - {}°{}".format(today.temperatureMin, today.temperatureMax, temp))
            em.add_field(name="Sunrise Time", value=sunrise)
            em.add_field(name="Sunset Time", value=sunset)
            em.add_field(name="Humidity", value="{0:.0f}%".format(now.humidity * 100))
            em.add_field(name="Wind Speed", value="{} {}".format(now.windSpeed, wind))
            em.add_field(name="Moon Phase", value=phase)
            em.add_field(name="Cloud Cover", value="{0:.0f}%".format(now.cloudCover * 100))
            em.add_field(name="Alerts", value=alerts)
            await ctx.send(embed=em)

    @commands.command()
    async def wiki(self, ctx, query: str):
        """
        Searches Wikipedia.
        """
        try:
            q = await ctx.bot.loop.run_in_executor(None, wikipedia.page, query)
            summary = await ctx.bot.loop.run_in_executor(None, wikipedia.summary, {"query": query, "sentences": 5})
            await ctx.send("{}:\n```\n{}\n```\nFor more information, visit <{}>"
                           .format(q.title, summary, q.url))
        except wikipedia.exceptions.PageError:
            await ctx.send("Either the page doesn't exist, or you typed it in wrong. Either way, please try again.")

    @commands.command(aliases=["meow"])
    async def cat(self, ctx):
        """
        A random cat!
        """
        with aiohttp.ClientSession() as sess:
            async with sess.get("http://random.cat/meow") as get:
                assert isinstance(get, aiohttp.ClientResponse)
                json = await get.json()
        file = await util.get_file(json["file"])
        await ctx.send(file=discord.File(filename="cat.{}".format(str(json["file"]).split(".")[-1]),
                                         fp=io.BytesIO(file)))

    @commands.command(aliases=["woof"])
    async def dog(self, ctx):
        """
        A random dog!
        """
        with aiohttp.ClientSession() as sess:
            async with sess.get("http://random.dog/woof") as get:
                assert isinstance(get, aiohttp.ClientResponse)
                _url = (await get.read()).decode("utf-8")
                url = "http://random.dog/" + str(_url)
        file = await util.get_file(url)
        await ctx.send(file=discord.File(filename=_url, fp=io.BytesIO(file)))


def setup(bot: DiscordBot):
    bot.add_cog(Internet(bot))
