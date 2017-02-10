"""
Dedicated Meme commands.
"""

import json
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
    async def meme_custom(self, ctx, pic: str, line1: str, line2: str):
        """Generates a meme using a custom picture."""
        if [".gif", "gifv"] not in pic[-5:]:
            i = random.randint(0, 9999)
            path = "mods/utils/images/other/tempimg{}.jpg".format(i)
            rep = [["-", "--"], ["_", "__"], ["?", "~q"], ["%", "~p"], [" ", "%20"], ["''", "\""]]
            for i in rep:
                line1 = line1.replace(i[0], i[1])
                line2 = line2.replace(i[0], i[1])
            link = "http://memegen.link/custom/{0}/{1}.jpg?alt={2}".format(line1, line2, pic)
            await util.download(link, path)
            await ctx.send(file=path)
            os.remove(path)
        else:
            await ctx.send("You can't use gifs for memes!")

    @meme.command(name="user")
    async def meme_user(self, ctx, user: discord.User, line1: str, line2: str):
        """Generates a meme on a users avatar."""
        i = random.randint(0, 9999)
        path = "mods/utils/images/other/tempimg{}.jpg".format(i)
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

    @meme_templates.command(name="search")
    async def templates__search(self, ctx, searchtype=None, *, query=None):
        """Searches the current usable meme templates.

            Don"t put in searchtype and query for a list of search types."""
        if not searchtype and not query:
            await ctx.send(
                "Search types include:\nName: Searches for the meme code of a meme.\n"
                "Example: Gives an example version of the given meme code.\n"
                "Aliases: Lists the possible alias meme codes for a meme.\nStyles: Lists alternate styles for a meme.")
        if searchtype == "name":
            url = "http://memegen.link/templates/"
            query = query.title()
            query = query.replace("'A", "'a").replace("'R", "'r").replace("'S", "'s").replace("'M", "'m")
            with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    resp = await resp.json()
            with open("mods/utils/json/fun/memenames.json", "w") as f:
                f.seek(0)
                f.write(json.dumps(resp))
                f.truncate()
            with open("mods/utils/json/fun/memenames.json") as f:
                names = json.load(f)
            if query in names:
                q = names[query]
                await ctx.send(q[30:])
            else:
                await ctx.send("That isn't a real meme!")
        if searchtype == "example":
            i = random.randint(0, 9999)
            path = "mods/utils/images/other/tempimg{}.jpg".format(i)
            link = "http://memegen.link/{0}/your-text/goes-here.jpg".format(query)
            await util.download(link, path)
            await ctx.send(file=path)
            os.remove(path)
        if searchtype == "aliases":
            url = "http://memegen.link/templates/{}".format(query)
            with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    resp = await resp.json()
            if len(resp["aliases"]) > 1:
                await ctx.send("Aliases for {0} are `".format(query) + ", ".join(map(str, resp["aliases"] + "`")))
            else:
                await ctx.send("There are no aliases for this meme.")
        if searchtype == "styles":
            url = "http://memegen.link/templates/{}".format(query)
            with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    resp = await resp.json()
            if len(resp["styles"]) > 0:
                await ctx.send(
                    "Alternative styles for {0} are `".format(query) + ", ".join(map(str, resp["styles"])) + "`")
            else:
                await ctx.send("There are no alternative styles for this meme.")


def setup(bot: DiscordBot):
    bot.add_cog(Meme(bot))
