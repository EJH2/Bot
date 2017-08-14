"""
Dedicated Meme commands.
"""
import io
import urllib.parse

import aiohttp
import discord
from discord.ext import commands

from discordbot.bot import DiscordBot
from discordbot.cogs.utils import util


class Meme:
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def meme(self, ctx, meme: str, line1: str, line2: str, style=""):
        """
        Generates a meme.
        
        Use the meme templates command to see a list of valid memes.
        """
        rep = [["-", "--"], ["_", "__"], ["?", "~q"], ["%", "~p"], [" ", "%20"], ["''", "\""]]
        for i in rep:
            line1 = line1.replace(i[0], i[1])
            line2 = line2.replace(i[0], i[1])
        if not style:
            link = f"http://memegen.link/{meme}/{line1}/{line2}.jpg"
        else:
            link = f"http://memegen.link/{meme}/{line1}/{line2}.jpg?alt={style}"
        file = await util.get_file(self.bot, link)
        await ctx.send(file=discord.File(fp=io.BytesIO(file), filename="meme.png"))

    @meme.command(name="custom")
    async def meme_custom(self, ctx, link: str, line1: str, line2: str):
        """
        Generates a meme using a custom picture.
        """
        async with self.bot.session.get(link) as get:
            assert isinstance(get, aiohttp.ClientResponse)
            content = get.headers['Content-Type']
            type_split = content.split("/")
            if type_split[0] == "image" and type_split[1] in ["png", "jpeg", "bmp"]:
                rep = [["-", "--"], ["_", "__"], ["?", "~q"], ["%", "~p"], [" ", "%20"], ["''", "\""]]
                for i in rep:
                    line1 = line1.replace(i[0], i[1])
                    line2 = line2.replace(i[0], i[1])
                link = f"http://memegen.link/custom/{line1}/{line2}.jpg?alt={link}"
                file = await util.get_file(self.bot, link)
                await ctx.send(file=discord.File(fp=io.BytesIO(file), filename="meme.png"))
            else:
                await ctx.send("Only jpeg, png, or bmp images please!")

    @meme.command(name="user")
    async def meme_user(self, ctx, user: discord.User, line1: str, line2: str):
        """
        Generates a meme on a users avatar.
        """
        rep = [["-", "--"], ["_", "__"], ["?", "~q"], ["%", "~p"], [" ", "%20"], ["''", "\""]]
        for i in rep:
            line1 = line1.replace(i[0], i[1])
            line2 = line2.replace(i[0], i[1])
        link = f"http://memegen.link/custom/{line1}/{line2}.jpg?alt={user.avatar_url}"
        file = await util.get_file(self.bot, link)
        await ctx.send(file=discord.File(fp=io.BytesIO(file), filename="meme.gif"))

    @meme.group(name="templates", invoke_without_command=True)
    async def meme_templates(self, ctx):
        """
        Gives users a list of meme templates.
        """
        async with self.bot.session.get("http://memegen.link/templates/") as resp:
            resp = await resp.json()
        memes = [resp[key][35:] for key in resp]
        await ctx.send(f"All stock templates are: {', '.join(memes)}")

    @commands.command(aliases=["illegal"])
    async def trump(self, ctx, *, meme: str):
        """
        Generates an extra spicy trump meme.
        """
        meme = urllib.parse.quote_plus(meme)
        link = f"http://martmists.com/api/v1/illegal?query={meme}"
        file = await util.get_file(self.bot, link)
        await ctx.send(file=discord.File(fp=io.BytesIO(file), filename="meme.gif"))


def setup(bot: DiscordBot):
    bot.add_cog(Meme(bot))
