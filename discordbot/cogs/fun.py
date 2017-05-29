"""
Fun commands.
"""

import asyncio
import io
import random
from urllib.parse import quote_plus

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import BucketType
from pyfiglet import figlet_format

from discordbot.bot import DiscordBot
from discordbot.cogs.utils import util

rr_bullet = random.randint(1, 6)
rr_count = 1


# noinspection PyTypeChecker
class Fun:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.command()
    async def shoot(self, ctx, *members: discord.Member):
        """
        Allows the user to shoot a person of choice.
        """
        if not members:
            await ctx.send("You gotta give me someone to work with here!")
            return
        for member in members:
            if member.id == self.bot.user.id:
                gif = await util.get_file("http://i.imgur.com/hPL5TGD.gif")
                await ctx.send(
                    "You attempted to shoot me, {}, but I dodged it!".format(ctx.message.author.name),
                    file=io.BytesIO(gif), filename="gif.gif")
            elif member.id == ctx.message.author.id:
                gif = await util.get_file("https://media.giphy.com/media/5xaOcLAo1Gg0oRgBz0Y/giphy.gif")
                await ctx.send(
                    "{} committed suicide!".format(ctx.message.author.name), file=io.BytesIO(gif), filename="gif.gif")
            else:
                gif = await util.get_file("https://s-media-cache-ak0.pinimg.com/originals/2d/fa/a9/"
                                          "2dfaa995a09d81a07cad24d3ce18e011.gif")
                await ctx.send(
                    "{1} was shot dead by the mighty {0}!".format(ctx.message.author.name, member.name),
                    file=io.BytesIO(gif), filename="gif.gif")

    @commands.command()
    async def rr(self, ctx):
        """Allows the user to take part in the famous Russian Pastime."""
        await ctx.send('You spin the cylinder of the revolver with 1 bullet in it...')
        await asyncio.sleep(1)
        await ctx.send('...you place the muzzle against your head and pull the trigger...')
        await asyncio.sleep(2)
        global rr_bullet, rr_count
        if rr_bullet == rr_count:
            await ctx.send('...your brain gets splattered all over the wall.')
            rr_bullet = random.randint(1, 6)
            rr_count = 1
        else:
            await ctx.send('...you live to see another day.')
            rr_count += 1

    @commands.command()
    async def lmgtfy(self, ctx, *, query: str):
        """
        Gives the user a "Let Me Google That For You" link.
        """
        await ctx.send("http://lmgtfy.com/?q={}".format(quote_plus(query)))

    @commands.command()
    async def meh(self, ctx):
        """
        Meh.
        """
        await ctx.send("¯\_(ツ)_/¯")

    @commands.command()
    async def say(self, ctx, *, message: str):
        """
        Makes the bot say anything the user wants it to.
        """
        await ctx.send(message)

    @commands.command(aliases=["out"])
    async def nope(self, ctx):
        """Gives a user a 'nope' gif."""
        nopes = [
            "https://giphy.com/gifs/reaction-nope-oh-god-why-dqmpS64HsNvb2",
            "https://i.imgur.com/2YeDA.jpg",
            "http://giphy.com/gifs/morning-good-reaction-ihWcaj6R061wc"
            ]
        await ctx.send(random.choice(nopes))

    @commands.command()
    async def timer(self, ctx, seconds: int, *, remember: str = ""):
        """
        Sets a timer for a user with the option of setting a reminder text.
        """
        if not remember:
            await ctx.send("{}, you have set a timer for {} seconds!".format(ctx.message.author.mention, seconds))
            end_timer = ctx.send("{}, your timer for {} seconds has expired!".format(ctx.message.author.mention,
                                 seconds))

        else:
            await ctx.send("{}, I will remind you about `{}` in {} seconds!".format(ctx.message.author.mention,
                                                                                    remember, seconds))
            end_timer = ctx.send("{}, your timer for {} seconds has expired! I was instructed to remind you about "
                                 "`{}`!".format(ctx.message.author.mention, seconds, remember))

        def check(m):
            return m.author == ctx.message.author and m.content == "{0.bot.command_prefix}cancel".format(
                ctx)
        try:
            timer = await ctx.bot.wait_for("message", check=check, timeout=seconds)
            if timer:
                await ctx.send("{}, Cancelling your timer...".format(ctx.message.author.mention))
        except asyncio.TimeoutError:
            await end_timer
            return

    @commands.command()
    async def shame(self, ctx):
        """
        Let the shame bells ring!
        """
        await ctx.send(":bell::bell::bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ "
                       "​:bell: ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​:bell:"
                       " ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​:bell::bell:"
                       ":bell:\n:bell: ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​:bell:"
                       " ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell:"
                       " ​ ​ ​ ​ ​ ​ ​:bell::bell::bell::bell: ​ ​ ​ ​ ​ ​:bell:\n:bell:"
                       ":bell::bell: ​ ​ ​ ​ ​ ​ ​:bell::bell::bell:"
                       " ​ ​ ​ ​ ​ ​ ​:bell::bell::bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​:bell:"
                       " ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell::bell::bell:\n"
                       "              :bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell:"
                       " ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ "
                       "​ ​ ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell:\n:bell::bell:"
                       ":bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell:"
                       " ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​:bell:"
                       " ​ ​ ​ ​ ​ ​ ​:bell::bell:​:bell:\n")

    @commands.command()
    async def fancify(self, ctx, *, text: str):
        """
        "Fancy-ify" text.
        """
        output = ""
        for letter in text:
            if 65 <= ord(letter) <= 90:
                output += chr(ord(letter) + 119951)
            elif 97 <= ord(letter) <= 122:
                output += chr(ord(letter) + 119919)
            elif letter == " ":
                output += " "
        await ctx.send(output)

    @commands.command()
    async def bigtext(self, ctx, *, text):
        """
        Create enlarged text.
        """
        await ctx.send("```fix\n" + figlet_format(text, font="big") + "```")

    @commands.command()
    @commands.cooldown(1, 20, BucketType.channel)
    async def repeat(self, ctx, times: int, *, content: str):
        """
        Repeats a message x times.
        """
        if times > 50:
            await ctx.send("I can't repeat that that many times! I might choke!")
            return
        for x in range(0, times):
            await ctx.send(content)
            await asyncio.sleep(1)
        await ctx.send("Done!")

    @commands.command(aliases=["8ball"])
    async def eightball(self, ctx, *, question: str):
        """
        Receive a response from the mighty eight ball.
        """
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
        await ctx.send("{0.author} asked `{1}`, and the magic eight ball replied `{2}`".format(
            ctx.message, question, random.choice(responses)
        ))

    @commands.command()
    async def copypasta(self, ctx, query: int = None):
        """Gives the user a random copypasta.

        Do `^copypasta <number from 1-22>` for a specific copypasta!
        """
        with io.open('discordbot/cogs/utils/files/copypasta.txt', 'r', encoding='utf8') as f:
            data = f.readlines()
        if query:
            query_req = 1 <= query <= len(data)
            line = "Query must be from 1 to {}!".format(len(data))
            if query_req:
                line = data[query - 1]
        else:
            line = random.choice(data)
        await ctx.send(line)

    @commands.command()
    async def lenny(self, ctx):
        """
        Lenny faces!
        """
        with aiohttp.ClientSession() as sess:
            async with sess.get("http://lenny.today/api/v1/random") as get:
                assert isinstance(get, aiohttp.ClientResponse)
                lenny = await get.json()
                await ctx.send(lenny[0]["face"])

    @commands.command()
    async def scramble(self, ctx, word_length: int = None):
        """Allows the user to play a word scramble with the bot."""
        with aiohttp.ClientSession() as sess:
            if word_length:
                word_length_req = 3 <= word_length <= 20
                if word_length_req:
                    async with sess.get("http://www.setgetgo.com/randomword/get.php?len={}".format(word_length)) as get:
                        assert isinstance(get, aiohttp.ClientResponse)
                        word = await get.read()
                else:
                    await ctx.send("Word length must be within 3 and 20!")
                    return
            else:
                async with sess.get("http://www.setgetgo.com/randomword/get.php") as get:
                    assert isinstance(get, aiohttp.ClientResponse)
                    word = await get.read()
        word = word.decode()
        print(word)
        scrambled = random.sample(word, len(word))
        scrambled = ''.join(scrambled)
        await ctx.send("The word scramble is: `{}`! You have 30 seconds to solve...".format(scrambled))

        def check(m):
            return m.content == word and m.channel == ctx.message.channel
        try:
            msg = await ctx.bot.wait_for("message", check=check, timeout=30)
            if msg:
                await ctx.send("Nice job! {} solved the scramble! The word was `{}`!".format(msg.author.name, word))
        except asyncio.TimeoutError:
            await ctx.send("Oops! Nobody solved it. The word was `{}`!".format(word))

    @commands.command()
    async def roti(self, ctx, *, number: int = None):
        """
        Bestows the user with the Rules of the Internet.
        """
        with io.open('discordbot/cogs/utils/files/RulesOTI.txt', 'r', encoding='utf8') as f:
            data = f.readlines()
        if number:
            query_req = 1 <= number <= len(data)
            line = "Number must be from 1 to {}!".format(len(data))
            if query_req:
                line = data[number - 1]
        else:
            line = random.choice(data)
        await ctx.send(line)

    @commands.command()
    async def whoosh(self, ctx):
        """
        Whoosh!
        """
        await ctx.send(file=discord.File(fp="discordbot/cogs/utils/files/overhead.png"))

    @commands.command(aliases=["pybelike"])
    async def python(self, ctx):
        """
        Gives an accurate XKCD representation of Python.
        """
        await ctx.send(file=discord.File(fp="discordbot/cogs/utils/files/python.png"))

    @commands.command(aliases=["star"])
    async def goldstar(self, ctx):
        """
        You get a gold star!
        """
        await ctx.send(file=discord.File(fp="discordbot/cogs/utils/files/goldstar.png"))

    @commands.command()
    async def tried(self, ctx):
        """
        At least you tried...
        """
        await ctx.send(file=discord.File(fp="discordbot/cogs/utils/files/tried.png"))

    @commands.command()
    async def works(self, ctx):
        """
        It worked for me ¯\_(ツ)_/¯
        """
        await ctx.send(file=discord.File(fp="discordbot/cogs/utils/files/works.png"))


def setup(bot: DiscordBot):
    bot.add_cog(Fun(bot))
