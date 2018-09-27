"""
Commands for the bot that come from the internet.
"""
import datetime
import functools
import io
import re

import aiohttp
import astral
import darksky
import discord
import geocoder
import pytz
import wikipedia
import wikipedia.exceptions
import xkcd
from bs4 import BeautifulSoup as BSoup
from discord.ext import commands

from discordbot.main import DiscordBot
from discordbot.utils import checks, util


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
    """
    Commands for the bot that come from the internet.
    """

    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.command()
    async def rip(self, ctx, user: str = None):
        """RIP."""
        if user is None:
            user = ctx.author.display_name
        await ctx.send(f"<http://ripme.xyz/{user.replace(' ', '%20')}>")

    @commands.command()
    async def robohash(self, ctx, user: str = None):
        """Robot pics."""
        if user is None:
            user = ctx.author.display_name
        url = f"https://robohash.org/{user.replace(' ', '%20')}.png"
        file = await util.get_file(self.bot, url)
        await ctx.send(file=discord.File(fp=io.BytesIO(file), filename="robot.png"))

    @commands.command()
    @commands.check(checks.needs_embed)
    async def xkcd(self, ctx, query: int = None):
        """Queries a random XKCD comic.

        Do xkcd <number> to pick a specific comic.
        Alternatively, do ^xkcd to get the latest comic!"""
        if query == 404:
            em = discord.Embed(color=discord.Color.red())
            em.title = "\N{CROSS MARK} Error"
            em.description = "Error 404: Comic Not Found"
            return await ctx.send(embed=em)
        latest_comic = xkcd.getLatestComicNum()
        if query:
            query_req = 1 <= int(query) <= int(latest_comic)
            if query_req:
                comic = xkcd.getComic(query)
            else:
                em = discord.Embed(color=discord.Color.red())
                em.title = "\N{CROSS MARK} Error"
                em.description = f"It has to be between 1 and {str(latest_comic)}!"
                return await ctx.send(embed=em)
        else:
            comic = xkcd.getRandomComic()
        embed = discord.Embed(title=f"xkcd {comic.number}: {comic.title}", url=comic.link)

        embed.set_image(url=comic.imageLink)
        embed.set_footer(text=comic.altText)

        await ctx.send(embed=embed)

    @commands.command()
    async def weather(self, ctx, *, location):
        """Gives the current weather in a city."""
        key = self.bot.config["bot"].get("WeatherKey", None)
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
            now_time_ = datetime.datetime.fromtimestamp(int(now.time), tz=pytz.timezone(forecast.timezone))
            now_time = now_time_.strftime('%H:%M:%S')
            phase = get_moon_phase(now_time_)
            try:
                _alerts = []
                alerts = "None"
                for i in forecast.alerts:
                    i.expires = datetime.datetime.fromtimestamp(int(i.expires)).strftime("%A, %B %d at %H:%M:%S")
                    i.regions = ", ".join(i.regions)
                    i.severity = i.severity.title()
                    _alerts += [f"[{str(i.severity)}: {str(i.title)} in {str(i.regions)}]({str(i.uri)} "
                                f"'Click for Full Description'): Expires on {str(i.expires)}\n"]
                    alerts = "\n".join(_alerts)
            except AttributeError:
                alerts = "None"
            unit = forecast.flags.units
            units = {"us": ["F", "Miles/Hour"], "si": ["C", "Meters/Second"], "ca": ["C", "Kilometers/Hour"], "uk2":
                ["C", "Miles/Hour"]}
            em = discord.Embed(title=f"Weather in {loc} at {now_time}",
                               description="Here is today's forecast:")
            em.set_thumbnail(url=f"https://discord.lol-sa.me/files/weather/{today.icon}.png" if today.icon in
                                                                                                ["clear-day",
                                                                                                 "clear-night", "rain",
                                                                                                 "snow", "sleet",
                                                                                                 "wind", "fog",
                                                                                                 "cloudy",
                                                                                                 "partly-cloudy-day",
                                                                                                 "partly-cloudy-night"] else None)
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
            em.add_field(name="Temp Range", value=f"{today.temperatureMin} - {today.temperatureMax}°{units[unit][0]}")
            em.add_field(name="Sunrise Time", value=sunrise)
            em.add_field(name="Sunset Time", value=sunset)
            em.add_field(name="Humidity", value=f"{now.humidity * 100:.0f}%")
            em.add_field(name="Wind Speed", value=f"{now.windSpeed} {units[unit][1]}")
            em.add_field(name="Moon Phase", value=phase)
            em.add_field(name="Cloud Cover", value=f"{now.cloudCover * 100:.0f}%")
            em.add_field(name="Alerts", value=alerts)
            await ctx.send(embed=em)

    @commands.command()
    async def wiki(self, ctx, query: str):
        """Searches Wikipedia."""
        try:
            q = await ctx.bot.loop.run_in_executor(None, wikipedia.page, query)
            summary = await ctx.bot.loop.run_in_executor(None, wikipedia.summary, {"query": query, "sentences": 5})
            await ctx.send(f"{q.title}:\n```\n{summary}\n```\nFor more information, visit <{q.url}>")
        except wikipedia.exceptions.PageError:
            await ctx.send("Either the page doesn't exist, or you typed it in wrong. Either way, please try again.")

    @commands.command()
    async def color(self, ctx, *, color: str):
        """Returns a picture and a name of the requested color!

        Colors can be either hexadecimal or rgb."""
        regex = re.compile("#?([\d\w]{6}|[\d\w]{3})$|\(?(\d{1,3}), ?(\d{1,3}), ?(\d{1,3})\)?")
        match = regex.match(color)
        attrs = {"format": "json"}
        if match:
            # Hex vs. RGB values
            if match.group(1):
                attrs["hex"] = match.group()
            else:
                attrs["rgb"] = match.group()
        else:
            return await ctx.send("Sorry, but that is not a valid rgb or hex color.")
        color_api = "http://thecolorapi.com/id?"
        async with self.bot.session.get(color_api, params=attrs) as get:
            resp = await get.json()
        hex_code = str(resp["hex"]["clean"])
        contrast = str(resp["contrast"]["value"]).strip("#")
        name = str(resp["name"]["value"])
        image = f"http://placehold.it/300x300.png/{hex_code}/{contrast}&text={name}"
        pic = await util.get_file(self.bot, image)
        await ctx.send(file=discord.File(fp=io.BytesIO(pic), filename="color.png"))

    @commands.command(aliases=["meow"])
    async def cat(self, ctx):
        """A random cat!"""
        async with self.bot.session.get("http://random.cat/meow") as get:
            assert isinstance(get, aiohttp.ClientResponse)
            json = await get.json()
        file = await util.get_file(self.bot, json["file"])
        ext = str(json["file"]).split(".")[-1]
        await ctx.send(file=discord.File(filename=f"cat.{ext}", fp=io.BytesIO(file)))

    @commands.command(aliases=["woof"])
    async def dog(self, ctx):
        """A random dog!"""
        async with self.bot.session.get("http://random.dog/woof") as get:
            assert isinstance(get, aiohttp.ClientResponse)
            _url = (await get.read()).decode("utf-8")
            url = f"http://random.dog/{str(_url)}"
        file = await util.get_file(self.bot, url)
        await ctx.send(file=discord.File(filename=_url, fp=io.BytesIO(file)))

    @commands.command(aliases=["birb", "tweet"])
    async def bird(self, ctx):
        """A random bird!"""
        async with self.bot.session.get("http://random.birb.pw/tweet/") as get:
            assert isinstance(get, aiohttp.ClientResponse)
            _url = (await get.read()).decode("utf-8")
            url = f"http://random.birb.pw/img/{str(_url)}"
        file = await util.get_file(self.bot, url)
        await ctx.send(file=discord.File(filename=_url, fp=io.BytesIO(file)))

    @commands.command(aliases=["facts"])
    async def randomfacts(self, ctx):
        """Gives 3 random facts!"""
        async with self.bot.session.get("http://randomfactgenerator.net/") as get:
            assert isinstance(get, aiohttp.ClientResponse)
            _html = await get.read()
        html = BSoup(_html, 'html.parser')
        facts = []
        for fact in html.find_all(id="z"):
            facts.append(fact.contents[0])
        await ctx.send(f"Did you know?\n"
                       f"\t1. {facts[0]}\n"
                       f"\t2. {facts[1]}\n"
                       f"\t3. {facts[2]}")

    @commands.command(aliases=["dadjoke"])
    async def joke(self, ctx):
        """Sends a Dad Joke!"""
        headers = {"Accept": "application/json"}
        async with self.bot.session.get("https://icanhazdadjoke.com", headers=headers) as get:
            assert isinstance(get, aiohttp.ClientResponse)
            resp = await get.json()
            await ctx.send(resp["joke"])

    @commands.command()
    async def lenny(self, ctx):
        """Lenny faces!"""
        async with self.bot.session.get("http://lenny.today/api/v1/random") as get:
            assert isinstance(get, aiohttp.ClientResponse)
            lenny = await get.json()
            await ctx.send(lenny[0]["face"])


def setup(bot: DiscordBot):
    bot.add_cog(Internet(bot))
