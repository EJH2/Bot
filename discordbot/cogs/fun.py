"""
Fun commands.
"""

import asyncio
import io
import random

import aiohttp
import discord
from PIL import Image, ImageDraw
from discord.ext import commands
from discord.ext.commands import BucketType
from pyfiglet import figlet_format, FontNotFound

from discordbot.main import DiscordBot

rr_bullet = random.randint(1, 6)
rr_count = 1


class Fun:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def ascii(self, ctx, text: str, font: str, textcolor: str = '', background: str = ''):
        """Creates ASCII text."""
        if not textcolor:
            textcolor = "white"
        if not background:
            background = "black"
        if font == "barbwire":
            text = text.replace("", " ")
        img = Image.new('RGB', (2000, 1000))
        d = ImageDraw.Draw(img)
        try:
            d.text((20, 20), figlet_format(text, font=font), fill=(255, 0, 0))
            text_width, text_height = d.textsize(figlet_format(text, font=font))
            img1 = Image.new('RGB', (text_width + 30, text_height + 30), background)
            d = ImageDraw.Draw(img1)
            d.text((20, 20), figlet_format(text, font=font), fill=textcolor, anchor="center")
            temp = io.BytesIO()
            img1.save(temp, format="png")
            temp.seek(0)
            await ctx.send(file=discord.File(filename="ascii.png", fp=temp))
        except FontNotFound:
            await ctx.send(f"`{font}` seems to not be a valid font. Try looking here: "
                           "http://www.figlet.org/examples.html")

    @ascii.command(name="fonts")
    async def ascii_fonts(self, ctx):
        """Lists available ASCII fonts."""
        await ctx.send("All available fonts for the command can be found here: http://www.figlet.org/examples.html")

    @commands.command()
    async def fancify(self, ctx, *, text: str):
        """"Fancy-ify" text."""
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
        """Create enlarged text."""
        await ctx.send("```fix\n" + figlet_format(text, font="big") + "```")

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
    async def say(self, ctx, *, message: str):
        """Makes the bot say anything the user wants it to."""
        await ctx.send(message)

    @commands.command()
    @commands.cooldown(1, 20, BucketType.channel)
    async def repeat(self, ctx, times: int, *, content: str):
        """Repeats a message x times."""
        if times > 50:
            await ctx.send("I can't repeat that that many times! I might choke!")
            return
        for x in range(0, times):
            await ctx.send(content)
            await asyncio.sleep(1)
        await ctx.send("Done!")

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
                       f"`{random.choice(responses)}`")

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
            return m.content == word and m.channel == ctx.channel

        try:
            msg = await ctx.bot.wait_for("message", check=check, timeout=30)
            if msg:
                await ctx.send(f"Nice job! {msg.author.name} solved the scramble! The word was `{word}`!")
        except asyncio.TimeoutError:
            await ctx.send(f"Oops! Nobody solved it. The word was `{word}`!")


def setup(bot: DiscordBot):
    bot.add_cog(Fun(bot))
