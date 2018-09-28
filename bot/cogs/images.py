# coding=utf-8
"""File containing image related commands for the bot"""
import io
import random
import re
from urllib.parse import quote_plus

import aiohttp
import discord
from discord.ext import commands
from bot.main import Bot
from bot.utils import utils
from datetime import datetime as d
from PIL import Image
import base64


class Images:
    """Cog containing image related commands for the bot"""
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(aliases=["tombstone"])
    async def rip(self, ctx, user: discord.User = None, *, epitaph: str = ""):
        """RIP"""
        user = user or ctx.author
        try:
            user = ctx.guild.get_member(user.id)
        except discord.DiscordException:
            pass
        death = f"{user.created_at.strftime('%e %b, %Y')} to {d.now().strftime('%e %b, %Y')}"
        epitaph = epitaph + f": {death}" if epitaph else death
        str_to_encrypt = f"n={user.display_name}&e={epitaph}".encode()
        encrypted = base64.encodebytes(str_to_encrypt).decode()  # Encode parameters to base64
        url = f"http://www.oregontrailtombstone.com/tombstone.php?p={encrypted}"

        page = self.bot.browser_page
        if page is None:
            await self.bot.create_browser()
        await page.goto(url)
        tombstone = (await page.JJ('div'))[1]  # Select second page div containing the tombstone image
        file = await tombstone.screenshot({"type": "png"})

        im = Image.open(io.BytesIO(file))
        im = im.convert('RGBA')

        datas = im.getdata()
        new_data = []
        for item in datas:
            if item[0] == 0 and item[1] == 0 and item[2] == 0:
                new_data.append((0, 0, 0, 0))
            else:
                new_data.append(item)

        im.putdata(new_data)
        img_array = io.BytesIO()
        im.save(img_array, format="PNG")
        file = img_array.getvalue()
        await ctx.send(file=discord.File(fp=io.BytesIO(file), filename="rip.png"))

    @commands.command()
    async def color(self, ctx, *, color: str):
        """Returns a picture and a name of the requested color!

        Colors can be either hexadecimal or rgb."""
        regex = re.compile("#?([\d\w]{6}|[\d\w]{3})$|\(?(\d{1,3}), ?(\d{1,3}), ?(\d{1,3})\)?")
        match = regex.match(color)
        attrs = {"format": "json"}
        if match:
            # Hex vs. RGB values
            if match.group(1):
                attrs["hex"] = match.group()
            else:
                attrs["rgb"] = match.group()
        else:
            return await ctx.send("Sorry, but that is not a valid rgb or hex color.")
        color_api = "http://thecolorapi.com/id?"
        async with self.bot.session.get(color_api, params=attrs) as get:
            resp = await get.json()
        hex_code = str(resp["hex"]["clean"])
        contrast = str(resp["contrast"]["value"]).strip("#")
        name = str(resp["name"]["value"])
        image = f"http://placehold.it/300x300.png/{hex_code}/{contrast}&text={name}"
        pic = await utils.get_file(self.bot, image)
        await ctx.send(file=discord.File(fp=io.BytesIO(pic), filename="color.png"))
        
    @commands.command()
    async def shoot(self, ctx, member: discord.User = None):
        """Allows the user to shoot a person of choice."""
        if not member:
            return await ctx.send("You gotta give me someone to work with here!")

        if member == self.bot.user:
            gif = random.choice([
                "bot/files/gun_dodge1.gif",
                "bot/files/gun_dodge2.gif",
                "bot/files/gun_dodge3.gif"
            ])
            message = f"You attempted to shoot me, {ctx.author.name}, but I dodged it!"

        elif member == ctx.author:
            gif = random.choice([
                "bot/files/gun_suicide1.gif",
                "bot/files/gun_suicide2.gif",
                "bot/files/gun_suicide3.gif",
                "bot/files/gun_suicide4.gif"
            ])
            message = f"{ctx.author.name} committed suicide!"

        else:
            gif = random.choice([
                "bot/files/gun_shooting1.gif",
                "bot/files/gun_shooting2.gif",
                "bot/files/gun_shooting3.gif",
                "bot/files/gun_shooting4.gif",
                "bot/files/gun_shooting5.gif",
                "bot/files/gun_shooting6.gif",
                "bot/files/gun_shooting7.gif"
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
                "bot/files/stab_dodge1.gif",
                "bot/files/stab_dodge2.webp",
                "bot/files/stab_dodge3.gif",
                "bot/files/stab_dodge4.gif"
            ])
            message = f"You attempted to stab me, {ctx.author.name}, but I dodged it!"

        elif member == ctx.author:
            gif = random.choice([
                "bot/files/stab_suicide1.gif",
                "bot/files/stab_suicide2.gif",
                "bot/files/stab_suicide3.gif"
            ])
            message = f"{ctx.author.name} died to their own blade!"

        else:
            gif = random.choice([
                "bot/files/stab_stabbing1.gif",
                "bot/files/stab_stabbing2.gif",
                "bot/files/stab_stabbing3.gif",
                "bot/files/stab_stabbing4.gif"
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
                "bot/files/punch_dodge1.gif",
                "bot/files/punch_dodge2.gif",
                "bot/files/punch_dodge3.gif",
                "bot/files/punch_dodge4.gif",
                "bot/files/punch_dodge5.gif"
            ])
            message = f"You attempted to punch me, {ctx.author.name}, but I dodged it!"

        elif member == ctx.author:
            gif = random.choice([
                "bot/files/punch_self1.gif",
                "bot/files/punch_self2.gif",
                "bot/files/punch_self3.gif"
            ])
            message = f"{ctx.author.name} punched their self!"

        else:
            gif = random.choice([
                "bot/files/punch_punch1.gif",
                "bot/files/punch_punch2.gif",
                "bot/files/punch_punch3.gif",
                "bot/files/punch_punch4.gif",
                "bot/files/punch_punch5.gif"
            ])
            message = f"{member.name} was punched by the mighty {ctx.author.name}!"

        await ctx.send(message, file=discord.File(gif, filename=gif.split("/")[-1]))

    @commands.command()
    async def robohash(self, ctx, *, string: str = None):
        """Robot pics."""
        if string is None:
            string = ctx.author.display_name
        url = f"https://robohash.org/{quote_plus(string)}.png"
        file = await utils.get_file(self.bot, url)
        await ctx.send(file=discord.File(fp=io.BytesIO(file), filename="robot.png"))

    @commands.command()
    async def color(self, ctx, *, color: str):
        """Returns a picture and a name of the requested color!

        Colors can be either hexadecimal or rgb."""
        regex = re.compile("#?([\d\w]{6}|[\d\w]{3})$|\(?(\d{1,3}), ?(\d{1,3}), ?(\d{1,3})\)?")
        match = regex.match(color)
        attrs = {"format": "json"}
        if match:
            # Hex vs. RGB values
            if match.group(1):
                attrs["hex"] = match.group()
            else:
                attrs["rgb"] = match.group()
        else:
            return await ctx.send("Sorry, but that is not a valid rgb or hex color.")
        color_api = "http://thecolorapi.com/id?"
        async with self.bot.session.get(color_api, params=attrs) as get:
            resp = await get.json()
        hex_code = str(resp["hex"]["clean"])
        contrast = str(resp["contrast"]["value"]).strip("#")
        name = str(resp["name"]["value"])
        image = f"http://placehold.it/300x300.png/{hex_code}/{contrast}&text={name}"
        pic = await utils.get_file(self.bot, image)
        await ctx.send(file=discord.File(fp=io.BytesIO(pic), filename="color.png"))

    @commands.command(aliases=["meow"])
    async def cat(self, ctx):
        """A random cat!"""
        async with self.bot.session.get("http://aws.random.cat/meow") as get:
            assert isinstance(get, aiohttp.ClientResponse)
            json = await get.json()
        file = await utils.get_file(self.bot, json["file"])
        ext = str(json["file"]).split(".")[-1]
        await ctx.send(file=discord.File(filename=f"cat.{ext}", fp=io.BytesIO(file)))

    @commands.command(aliases=["woof"])
    async def dog(self, ctx):
        """A random dog!"""
        async with self.bot.session.get("http://random.dog/woof") as get:
            assert isinstance(get, aiohttp.ClientResponse)
            _url = (await get.read()).decode("utf-8")
            url = f"http://random.dog/{str(_url)}"
        file = await utils.get_file(self.bot, url)
        await ctx.send(file=discord.File(filename=_url, fp=io.BytesIO(file)))

    @commands.command(aliases=["birb", "tweet"])
    async def bird(self, ctx):
        """A random bird!"""
        async with self.bot.session.get("http://random.birb.pw/tweet/") as get:
            assert isinstance(get, aiohttp.ClientResponse)
            _url = (await get.read()).decode("utf-8")
            url = f"http://random.birb.pw/img/{str(_url)}"
        file = await utils.get_file(self.bot, url)
        await ctx.send(file=discord.File(filename=_url, fp=io.BytesIO(file)))


def setup(bot: Bot):
    """Setup function for the cog"""
    bot.add_cog(Images(bot))
