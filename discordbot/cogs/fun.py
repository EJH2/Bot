"""
Fun commands.
"""

import asyncio
import random

import discord
from discord.ext import commands
from discord.ext.commands import BucketType
from pyfiglet import figlet_format

from discordbot.bot import DiscordBot

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
                await ctx.send(
                    "You attempted to shoot me, {}, but I dodged it!\n"
                    "http://45.media.tumblr.com/c1165e983042a9cd1f17028a1c78170b/tumblr_n9c38m14291s5f9ado1_500.gif"
                    .format(ctx.message.author.name))
            elif member.id == ctx.message.author.id:
                await ctx.send(
                    "{} committed suicide!\nhttps://media.giphy.com/media/5xaOcLAo1Gg0oRgBz0Y/giphy.gif".format(
                        ctx.message.author.name))
            else:
                await ctx.send(
                    "{1} was shot dead by the mighty {0}!\n"
                    "https://s-media-cache-ak0.pinimg.com/originals/2d/fa/a9/2dfaa995a09d81a07cad24d3ce18e011.gif"
                    .format(ctx.message.author.name, member.name))

    @commands.command()
    async def rr(self, ctx):
        """Allows the user to take part in the famous Russian Pasttime."""
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
        msg = query.replace(" ", "+")
        msg = "http://lmgtfy.com/?q={}".format(msg)
        await ctx.send(msg)

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

    @commands.command()
    async def timer(self, ctx, seconds: int, *, remember: str = ""):
        """
        Sets a timer for a user with the option of setting a reminder text.
        """
        if not remember:
            end_timer = ctx.send("{}, your timer for {} seconds has expired!".format(ctx.message.author.name,
                                                                                         seconds))
            await ctx.send("{}, you have set a timer for {} seconds!".format(ctx.message.author.name, seconds))

            def check(m):
                return m.author == ctx.message.author and ctx.message.content == "{0.bot.command_prefix}cancel".format(
                    ctx)
            timer = await ctx.wait_for(check=check, timeout=seconds)
            if timer is None:
                await end_timer
                return
            await ctx.send("{}, Cancelling your timer...".format(ctx.message.author.mention))
        else:
            end_timer = ctx.send("{}, your timer for {} seconds has expired! I was instructed to remind you about "
                                 "`{}`!".format(ctx.message.author.mention, seconds, remember))
            await ctx.send("{}, I will remind you about `{}` in {} seconds!".format(ctx.message.author.mention,
                                                                                    seconds, remember))

            def check(m):
                return m.author == ctx.message.author and ctx.message.content == "{0.bot.command_prefix}cancel".format(
                    ctx)
            timer = await ctx.wait_for(check=check, timeout=seconds)
            if timer is None:
                await end_timer
                return
            await ctx.send("{}, Cancelling your timer...".format(ctx.message.author.mention))

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
        Fancify text.
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


def setup(bot: DiscordBot):
    bot.add_cog(Fun(bot))
