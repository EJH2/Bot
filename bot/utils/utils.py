# coding=utf-8
"""Utilities for the bot"""
import aiohttp
import discord
from discord.ext import commands

from bot.main import Bot
from tabulate import tabulate

# Command converters


class SourceEntity(commands.Converter):
    """Custom converter for the source command"""

    async def convert(self, ctx, arg: str):
        """Converter function for the source command"""
        cmd = ctx.bot.get_command(arg)
        if cmd is not None:
            return cmd.callback

        cog = ctx.bot.get_cog(arg)
        if cog is not None:
            return cog.__class__

        module = ctx.bot.extensions.get(arg)
        if module is not None:
            return module

        raise commands.BadArgument(f'{arg} is neither a command, a cog, nor an extension.')


class GuildConverter(commands.Converter):
    """Custom converter for the lookup command"""

    async def convert(self, ctx, arg: int):
        """Converter function for the lookup command"""
        async with ctx.bot.http._session.get(f'https://discordapp.com/api/v6/guilds/{arg}/widget.json') as get:
            assert isinstance(get, aiohttp.ClientResponse)
            json = await get.json(encoding='utf-8')
            if get.status == 200:
                json['data_type'] = 'guild'
                return json
            elif get.status == 403:
                return {'data_type': 'guild_partial', 'id': arg}
            else:
                raise discord.NotFound(get, 'guild not found')


class UserConverter(commands.Converter):
    """Custom converter for the lookup command"""

    async def convert(self, ctx, arg):
        """Converter function for the lookup command"""
        try:
            match = commands.UserConverter()._get_id_match(arg) or re.match(r'<@!?([0-9]+)>$', arg)
            user = None

            if match is not None:
                user_id = int(match.group(1))
                result = ctx.bot.get_user(user_id)
                if result:
                    user = result
                else:
                    user = await ctx.bot.get_user_info(match.group(1))
            assert isinstance(user, discord.User)
            return user
        except (AssertionError, Exception):
            raise discord.NotFound


class InviteUserGuild(commands.Converter):
    """Custom converter for the lookup command"""

    async def convert(self, ctx, arg):
        """Converter function for the lookup command"""
        try:
            return await commands.InviteConverter().convert(ctx, arg)
        except Exception:
            pass
            try:
                return await UserConverter().convert(ctx, arg)
            except Exception:
                try:
                    return await GuildConverter().convert(ctx, arg)
                except Exception:
                    raise commands.CommandError(f'`{arg}` could not be converted to Invite, User, or Guild')

# Utility functions


async def get_file(bot: Bot, url: str) -> bytes:
    """
    Get a file from the web using aiohttp.

    :param bot: DiscordBot instance to grab session.
    :param url: URL to get file from.
    :return: File bytes.
    """
    async with bot.session.get(url) as get:
        assert isinstance(get, aiohttp.ClientResponse)
        data = await get.read()
        return data


def neatly(entries: dict, colors="") -> str:
    """
    Neatly order text.

    :param entries: Entries to neat-ify.
    :param colors: Markdown code for Discord code blocks.
    :return: Neatened string.
    """
    entries = [[f'{entry}:', entries[entry]] for entry in entries]
    return f"```{colors}\n" \
           f"{tabulate(entries, tablefmt='plain', colalign=('right',))}\n" \
           f"```"
