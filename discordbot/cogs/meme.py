"""
Dedicated Meme commands.
"""

import os
import random

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
        """Generates a meme."""
        if ctx.invoked_subcommand is None:
            i = random.randint(0, 9999)
            path = "discordbot/cogs/utils/files/tempmeme{}.jpg".format(i)
            rep = [["-", "--"], ["_", "__"], ["?", "~q"], ["%", "~p"], [" ", "%20"], ["''", "\""]]
            for i in rep:
                line1 = line1.replace(i[0], i[1])
                line2 = line2.replace(i[0], i[1])
            if not style:
                link = "http://memegen.link/{0}/{1}/{2}.jpg".format(meme, line1, line2)
            else:
                link = "http://memegen.link/{0}/{1}/{2}.jpg?alt={3}".format(meme, line1, line2, style)
            await util.download(link, path)
            await ctx.send(file=path)
            os.remove(path)

    @meme.command(name="custom")
    async def meme_custom(self, ctx, link: str, line1: str, line2: str):
        """Generates a meme using a custom picture."""
        with aiohttp.ClientSession() as sess:
            async with sess.get(link) as get:
                assert isinstance(get, aiohttp.ClientResponse)
                content = get.headers['Content-Type']
                type_split = content.split("/")
                if type_split[0] == "image" and type_split[1] in ["png", "jpeg", "bmp"]:
                    i = random.randint(0, 9999)
                    path = "discordbot/cogs/utils/files/tempmeme{}.jpg".format(i)
                    rep = [["-", "--"], ["_", "__"], ["?", "~q"], ["%", "~p"], [" ", "%20"], ["''", "\""]]
                    for i in rep:
                        line1 = line1.replace(i[0], i[1])
                        line2 = line2.replace(i[0], i[1])
                    link = "http://memegen.link/custom/{0}/{1}.jpg?alt={2}".format(line1, line2, link)
                    await util.download(link, path)
                    await ctx.send(file=path)
                    os.remove(path)
                else:
                    await ctx.send("Only jpeg, png, or bmp images please!")

    @meme.command(name="user")
    async def meme_user(self, ctx, user: discord.User, line1: str, line2: str):
        """Generates a meme on a users avatar."""
        i = random.randint(0, 9999)
        path = "discordbot/cogs/utils/files/tempmeme{}.jpg".format(i)
        rep = [["-", "--"], ["_", "__"], ["?", "~q"], ["%", "~p"], [" ", "%20"], ["''", "\""]]
        for i in rep:
            line1 = line1.replace(i[0], i[1])
            line2 = line2.replace(i[0], i[1])
        link = "http://memegen.link/custom/{0}/{1}.jpg?alt={2}".format(line1, line2, user.avatar_url)
        await util.download(link, path)
        await ctx.send(file=path)
        os.remove(path)

    @meme.group(name="templates", invoke_without_command=True)
    async def meme_templates(self, ctx):
        """Gives users a list of meme templates."""
        await ctx.send("All stock templates can be found here: <{}>".format("http://memegen.link/templates/"))


def setup(bot: DiscordBot):
    bot.add_cog(Meme(bot))
