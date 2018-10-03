# coding=utf-8
"""File containing fun commands for the bot"""
import asyncio
import datetime
import functools
import io
import random

import aiohttp
import astral
import darksky
import discord
import geocoder
import pytz
import wikipedia
import xkcd
from bs4 import BeautifulSoup as BSoup
from discord.ext import commands
from pyfiglet import figlet_format

from bot.main import Bot


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


class Fun:
    """Cog containing fun commands for the bot"""

    def __init__(self, bot: Bot):
        self.bot = bot
        with io.open('bot/files/RulesOTI.txt', encoding='utf8') as f:
            self.rules = f.readlines()
        with io.open('bot/files/copypasta.txt', encoding='utf8') as f:
            self.copy = f.readlines()

    @commands.command()
    async def scramble(self, ctx):
        """Allows the user to play a word scramble with the bot."""
        async with self.bot.session.post("http://watchout4snakes.com/wo4snakes/Random/RandomWord") as post:
            assert isinstance(post, aiohttp.ClientResponse)
            word = await post.read()
        word = word.decode()
        print(word)
        scrambled = random.sample(word, len(word))
        scrambled = ''.join(scrambled)
        await ctx.send(f"The word scramble is: `{scrambled}`! You have 30 seconds to solve...")

        def check(m):
            """Checks to see if the word was posted in the correct channel"""
            return m.content == word and m.channel == ctx.channel

        try:
            msg = await ctx.bot.wait_for("message", check=check, timeout=30)
            if msg:
                await ctx.send(f"Nice job! {msg.author.mention} solved the scramble! The word was `{word}`!")
        except asyncio.TimeoutError:
            await ctx.send(f"Oops! Nobody solved it. The word was `{word}`!")

    @commands.command(aliases=["inspire", "inspireme"])
    async def inspiro(self, ctx):
        """Receive an inspiring auto-generated message."""
        async with self.bot.session.get("https://inspirobot.me/api?generate=true") as get:
            assert isinstance(get, aiohttp.ClientResponse)
            url = str(await get.read(), encoding='utf8')
        async with self.bot.session.get(url) as get:
            img = io.BytesIO(await get.read())
        await ctx.send(file=discord.File(img, filename=url))

    @commands.command()
    async def bigtext(self, ctx, *, text):
        """Create enlarged text."""
        await ctx.send("```fix\n" + figlet_format(text, font="big") + "```")

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

    @commands.command()
    async def xkcd(self, ctx, query: int = None):
        """Queries a random XKCD comic.

        Do xkcd <number> to pick a specific comic."""
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
        key = self.bot.config["extras"].get("darksky", None)
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
            units = {
                "us": ["F", "Miles/Hour"],
                "si": ["C", "Meters/Second"],
                "ca": ["C", "Kilometers/Hour"],
                "uk2": ["C", "Miles/Hour"]
            }
            w_types = ["clear-day", "clear-night", "rain", "snow", "sleet", "wind", "fog", "cloudy",
                       "partly-cloudy-day", "partly-cloudy-night"]
            em = discord.Embed(title=f"Weather in {loc} at {now_time}",
                               description="Here is today's forecast:")
            em.set_thumbnail(
                url=f"https://discord.lol-sa.me/files/weather/{today.icon}.png" if today.icon in w_types else None)
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
    async def wiki(self, ctx, *, query: str):
        """Searches Wikipedia."""
        try:
            q = await ctx.bot.loop.run_in_executor(None, wikipedia.page, query)
            summary = await ctx.bot.loop.run_in_executor(None, wikipedia.summary, *[query, 5])
            await ctx.send(f"{q.title}:\n```\n{summary}\n```\nFor more information, visit <{q.url}>")
        except wikipedia.exceptions.PageError:
            await ctx.send("Either the page doesn't exist, or you typed it in wrong. Either way, please try again.")

    @commands.command(aliases=["8ball"])
    async def eightball(self, ctx, *, question: str):
        """Receive a response from the mighty eight ball."""
        responses = [
            "It is certain",
            "It is decidedly so",
            "Without a doubt",
            "Yes, definitely",
            "You may rely on it",
            "As I see it, yes",
            "Most likely",
            "Outlook good",
            "Yes",
            "Signs point to yes",
            "Reply hazy, try again",
            "Ask again later",
            "Better not tell you now",
            "Cannot predict now",
            "Concentrate and ask again",
            "Don't count on it",
            "My reply is no",
            "My sources say no",
            "Outlook not so good",
            "Very doubtful"
        ]
        await ctx.send(f"{ctx.message.author} asked `{question}`, and the magic eight ball replied "
                       f"`{random.choice(responses)}`!")

    @commands.command(aliases=["choice"])
    async def choose(self, ctx, *options: commands.clean_content):
        """
        Chooses from a list of options.
        """
        if len(options) < 2:
            return await ctx.send("I don't have enough options to choose from!")

        await ctx.send(random.choice(options))

    @commands.command()
    async def copypasta(self, ctx, query: int = None):
        """Gives the user a random copypasta.

        Do `copypasta <number from 1-22>` for a specific copypasta!
        """
        if query:
            query_req = 1 <= query <= len(self.copy)
            line = f"Query must be from 1 to {len(self.copy)}!"
            if query_req:
                line = self.copy[query - 1]
        else:
            line = random.choice(self.copy)
        await ctx.send(line)

    @commands.command()
    async def roti(self, ctx, number: int = None):
        """Bestows the user with the Rules of the Internet.

        If no number is provided, then a random rule will be retrieved."""
        if number:
            query_req = 1 <= number <= len(self.rules)
            line = f"Number must be from 1 to {len(self.rules)}!"
            if query_req:
                line = self.rules[number - 1]
        else:
            line = random.choice(self.rules)
        await ctx.send(line)


def setup(bot: Bot):
    """Setup function for the cog"""
    bot.add_cog(Fun(bot))
