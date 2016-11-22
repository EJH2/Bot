"""
Fun commands.
"""

import asyncio

import discord
from discord.ext import commands
from discord.ext.commands import BucketType
from pyfiglet import figlet_format

from discordbot.bot import DiscordBot


# noinspection PyTypeChecker
class Fun:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def shoot(self, ctx, *members: discord.Member):
        """
        Allows the user to shoot a person of choice.
        """
        if not members:
            await self.bot.say("You gotta give me someone to work with here!")
            return
        for member in members:
            if member.id == self.bot.user.id:
                await self.bot.say(
                    "You attempted to shoot me, {}, but I dodged it!\n"
                    "http://45.media.tumblr.com/c1165e983042a9cd1f17028a1c78170b/tumblr_n9c38m14291s5f9ado1_500.gif"
                        .format(ctx.message.author.name))
            elif member.id == ctx.message.author.id:
                await self.bot.say(
                    "{} committed suicide!\nhttps://media.giphy.com/media/5xaOcLAo1Gg0oRgBz0Y/giphy.gif".format(
                        ctx.message.author.name))
            else:
                await self.bot.say(
                    "{1} was shot dead by the mighty {0}!\n"
                    "https://s-media-cache-ak0.pinimg.com/originals/2d/fa/a9/2dfaa995a09d81a07cad24d3ce18e011.gif"
                        .format(ctx.message.author.name, member.name))

    @commands.command()
    async def lmgtfy(self, *, query: str):
        """
        Gives the user a "Let Me Google That For You" link.
        """
        msg = query.replace(" ", "+")
        msg = "http://lmgtfy.com/?q={}".format(msg)
        await self.bot.say(msg)

    @commands.command()
    async def meh(self):
        """
        Meh.
        """
        await self.bot.say("¯\_(ツ)_/¯")

    @commands.command(pass_context=True)
    async def say(self, *, message: str):
        """
        Makes the bot say anything the user wants it to.
        """
        await self.bot.say(message)

    @commands.command(pass_context=True)
    async def timer(self, ctx, seconds: int, *, remember: str = ""):
        """
        Sets a timer for a user with the option of setting a reminder text.
        """
        if not remember:
            end_timer = self.bot.say("{}, your timer for {} seconds has expired!".format(ctx.message.author.name,
                                                                                         seconds))
            await self.bot.say("{}, you have set a timer for {} seconds!".format(ctx.message.author.name, seconds))
            await asyncio.sleep(float(seconds))
            await end_timer
        else:
            end_timer = self.bot.say("{}, your timer for {} seconds has expired! I was instructed to remind you about "
                                     "`{}`!".format(ctx.message.author.mention, seconds, remember))
            await self.bot.say("{}, I will remind you about `{}` in {} seconds!".format(ctx.message.author.mention,
                                                                                        seconds, remember))
            await asyncio.sleep(float(seconds))
            await end_timer

    @commands.command()
    async def shame(self):
        """
        Let the shame bells ring!
        """
        await self.bot.say(":bell::bell::bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ "
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
    async def fancify(self, *, text: str):
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
        await self.bot.say(output)

    @commands.command()
    async def bigtext(self, *, text):
        """
        Create enlarged text.
        """
        await self.bot.say("```fix\n" + figlet_format(text, font="big") + "```")

    @commands.command()
    @commands.cooldown(1, 20, BucketType.channel)
    async def repeat(self, times: int, *, content: str):
        """
        Repeats a message x times.
        """
        if times > 50:
            await self.bot.say("I can't repeat that that many times! I might choke!")
            return
        for x in range(0, times):
            await self.bot.say(content)
            await asyncio.sleep(1)
        await self.bot.say("Done!")


def setup(bot: DiscordBot):
    bot.add_cog(Fun(bot))
