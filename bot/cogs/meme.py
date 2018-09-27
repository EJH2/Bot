# coding=utf-8
"""Meme commands for the bot"""
import aiohttp
import io

import discord
from discord.ext import commands
from bot.main import Bot
from bot.utils import utils


class URLString(commands.Converter):
    """Converter for meme lines"""

    async def convert(self, ctx, argument):
        """Converter function for meme lines"""
        rep = {"-": "--", "_": "__", "?": "~q", "%": "~p", " ": "%20", "''": "\""}
        for i in rep:
            argument = argument.replace(i, rep[i])
        return argument


class Meme:
    """Cog containing meme commands for the bot"""
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def meme(self, ctx, meme: str, line1: URLString, line2: URLString, style: str = None):
        """Generates a meme.

        Use the meme templates command to see a list of valid memes.
        """
        style = f"?alt={style}" or ""
        link = f"http://memegen.link/{meme}/{line1}/{line2}.jpg{style}"
        file = await utils.get_file(self.bot, link)
        await ctx.send(file=discord.File(fp=io.BytesIO(file), filename="meme.png"))

    @meme.command(name="custom")
    async def meme_custom(self, ctx, link: str, line1: URLString, line2: URLString):
        """Generates a meme using a custom picture."""
        async with self.bot.session.get(link) as get:
            assert isinstance(get, aiohttp.ClientResponse)
            content = get.headers['Content-Type']
            type_split = content.split("/")
            if type_split[0] == "image" and type_split[1] in ["png", "jpeg", "bmp"]:
                link = f"http://memegen.link/custom/{line1}/{line2}.jpg?alt={link}"
                file = await utils.get_file(self.bot, link)
                await ctx.send(file=discord.File(fp=io.BytesIO(file), filename="meme.png"))
            else:
                await ctx.send("Only jpeg, png, or bmp images please!")

    @meme.command(name="user")
    async def meme_user(self, ctx, user: discord.User, line1: URLString, line2: URLString):
        """Generates a meme on a users avatar."""
        await ctx.invoke(self.meme_custom, link=user.avatar_url_as(format="png"), line1=line1, line2=line2)

    @meme.group(name="templates", invoke_without_command=True)
    async def meme_templates(self, ctx):
        """Gives users a list of meme templates."""
        async with self.bot.session.get("http://memegen.link/templates/") as resp:
            resp = await resp.json()
        memes = [resp[key][35:] for key in resp]
        await ctx.send(f"All stock templates are: {', '.join(memes)}")


def setup(bot: Bot):
    """Setup function for the cog"""
    bot.add_cog(Meme(bot))
