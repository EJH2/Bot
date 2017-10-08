"""
Image commands for the bot.
"""
import random

import discord
from discord.ext import commands

from discordbot.main import DiscordBot


class Image:
    """
    Image commands for the bot.
    """

    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.command()
    async def shoot(self, ctx, member: discord.User = None):
        """Allows the user to shoot a person of choice."""
        if not member:
            return await ctx.send("You gotta give me someone to work with here!")

        if member == self.bot.user:
            gif = random.choice([
                "discordbot/files/gifs/gun_dodge1.gif",
                "discordbot/files/gifs/gun_dodge2.gif",
                "discordbot/files/gifs/gun_dodge3.gif"
            ])
            message = f"You attempted to shoot me, {ctx.author.name}, but I dodged it!"

        elif member == ctx.author:
            gif = random.choice([
                "discordbot/files/gifs/gun_suicide1.gif",
                "discordbot/files/gifs/gun_suicide2.gif",
                "discordbot/files/gifs/gun_suicide3.gif",
                "discordbot/files/gifs/gun_suicide4.gif"
            ])
            message = f"{ctx.author.name} committed suicide!"

        else:
            gif = random.choice([
                "discordbot/files/gifs/gun_shooting1.gif",
                "discordbot/files/gifs/gun_shooting2.gif",
                "discordbot/files/gifs/gun_shooting3.gif",
                "discordbot/files/gifs/gun_shooting4.gif",
                "discordbot/files/gifs/gun_shooting5.gif",
                "discordbot/files/gifs/gun_shooting6.gif",
                "discordbot/files/gifs/gun_shooting7.gif"
            ])
            message = f"{member.name} was shot dead by the mighty {ctx.author.name}!"

        await ctx.send(message, file=discord.File(gif, filename=gif.split("/")[-1]))

    @commands.command()
    async def stab(self, ctx, member: discord.User = None):
        """Allows the user to stab a person of choice."""
        if not member:
            return await ctx.send("You gotta give me someone to work with here!")

        if member == self.bot.user:
            gif = random.choice([
                "discordbot/files/gifs/stab_dodge1.gif",
                "discordbot/files/gifs/stab_dodge2.webp",
                "discordbot/files/gifs/stab_dodge3.gif",
                "discordbot/files/gifs/stab_dodge4.gif"
            ])
            message = f"You attempted to stab me, {ctx.author.name}, but I dodged it!"

        elif member == ctx.author:
            gif = random.choice([
                "discordbot/files/gifs/stab_suicide1.gif",
                "discordbot/files/gifs/stab_suicide2.gif",
                "discordbot/files/gifs/stab_suicide3.gif"
            ])
            message = f"{ctx.author.name} died to their own blade!"

        else:
            gif = random.choice([
                "discordbot/files/gifs/stab_stabbing1.gif",
                "discordbot/files/gifs/stab_stabbing2.gif",
                "discordbot/files/gifs/stab_stabbing3.gif",
                "discordbot/files/gifs/stab_stabbing4.gif"
            ])
            message = f"{member.name} was stabbed to death by the mighty {ctx.author.name}!"

        await ctx.send(message, file=discord.File(gif, filename=gif.split("/")[-1]))

    @commands.command()
    async def punch(self, ctx, member: discord.User = None):
        """Allows the user to punch a person of choice."""
        if not member:
            return await ctx.send("You gotta give me someone to work with here!")

        if member == self.bot.user:
            gif = random.choice([
                "discordbot/files/gifs/punch_dodge1",
                "discordbot/files/gifs/punch_dodge2",
                "discordbot/files/gifs/punch_dodge3",
                "discordbot/files/gifs/punch_dodge4",
                "discordbot/files/gifs/punch_dodge5"
            ])
            message = f"You attempted to punch me, {ctx.author.name}, but I dodged it!"

        elif member == ctx.author:
            gif = random.choice([
                "discordbot/files/gifs/punch_self1",
                "discordbot/files/gifs/punch_self2",
                "discordbot/files/gifs/punch_self3"
            ])
            message = f"{ctx.author.name} punched their self!"

        else:
            gif = random.choice([
                "discordbot/files/gifs/punch_punch1",
                "discordbot/files/gifs/punch_punch2",
                "discordbot/files/gifs/punch_punch3",
                "discordbot/files/gifs/punch_punch4",
                "discordbot/files/gifs/punch_punch5"
            ])
            message = f"{member.name} was punched by the mighty {ctx.author.name}!"

        await ctx.send(message, file=discord.File(gif, filename=gif.split("/")[-1]))

    @commands.command(aliases=["out"])
    async def nope(self, ctx):
        """Gives a user a 'nope' gif."""
        nope = random.choice([
            "discordbot/files/gifs/nope1.gif",
            "discordbot/files/images/nope2.png",
            "discordbot/files/gifs/nope3.gif"
        ])
        await ctx.send(file=discord.File(nope, filename=nope.split("/")[-1]))

    @commands.command()
    async def whoosh(self, ctx):
        """Whoosh!"""
        await ctx.send(file=discord.File(fp="discordbot/files/images/overhead.png"))

    @commands.command(aliases=["pybelike"])
    async def python(self, ctx):
        """Gives an accurate XKCD representation of Python."""
        await ctx.send(file=discord.File(fp="discordbot/files/images/python.png"))

    @commands.command(aliases=["star"])
    async def goldstar(self, ctx):
        """You get a gold star!"""
        await ctx.send(file=discord.File(fp="discordbot/files/images/goldstar.png"))

    @commands.command()
    async def tried(self, ctx):
        """At least you tried..."""
        await ctx.send(file=discord.File(fp="discordbot/files/images/tried.png"))

    @commands.command()
    async def works(self, ctx):
        """It worked for me ¯\_(ツ)_/¯"""
        await ctx.send(file=discord.File(fp="discordbot/files/images/works.png"))


def setup(bot: DiscordBot):
    bot.add_cog(Image(bot))
