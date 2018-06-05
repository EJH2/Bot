# coding=utf-8
"""File containing informative commands for the bot"""
import aiohttp
import inspect
import re
import textwrap

import discord
from discord.ext import commands

from bot.main import Bot


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


class Info:
    """Cog containing informative commands for the bot"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def source(self, ctx, *, entity: SourceEntity):
        """Gets the source of the requested entity"""
        code = inspect.getsource(entity)
        code = textwrap.dedent(code).replace('`', '\u200b`')
        await ctx.send(f'```py\n{code}\n```')

    @commands.command(aliases=['alert'])
    async def suggest(self, ctx, *, suggestion: str):
        """Sends a message to the bot owner with your suggestion!"""
        await self.bot.app_info.owner.send(f'Suggestion received from {ctx.author} (ID: {ctx.author.id}) in {ctx.guild}'
                                           f' (ID: {ctx.guild.id}): {suggestion}')
        await ctx.send(f'{ctx.author.mention}, your suggestion has been sent to the owner!')

    @commands.command()
    async def lookup(self, ctx, *, id_number: InviteUserGuild):
        """Looks up an ID for a guild, user, or invite"""
        if isinstance(id_number, discord.Invite):
            inv = id_number
            embed = discord.Embed(title=f'Invite Code {inv.code}')
            inviter = f"{inv.inviter} ({inv.inviter.id})" if inv.inviter else "None"
            icon = inv.guild.icon_url_as(format='png') if isinstance(inv.guild, discord.Guild) else None
            embed.add_field(name='Statistics:',
                            value=f'Guild: {inv.guild.name} ({inv.guild.id})\n'
                                  f'Channel: #{inv.channel.name} ({inv.channel.id})\n'
                                  f'Created By: {inviter}')
            embed.set_thumbnail(url=icon) if icon is not None else None
            return await ctx.send(embed=embed)
        if isinstance(id_number, discord.User):
            user = id_number
            embed = discord.Embed(title=str(user))
            embed.add_field(name='Statistics:',
                            value=f'ID: {user.id}\n'
                                  f'Created At: {user.created_at}\n'
                                  f'Bot: {user.bot}')
            embed.set_thumbnail(url=id_number.avatar_url_as(static_format='png'))
            return await ctx.send(embed=embed)
        else:
            json = dict(id_number)
            if json['data_type'] == 'guild':
                rx = r'(?:https?\:\/\/)?(?:[a-zA-z]+\.)?discordapp\.com\/invite\/(.+)'
                m = re.match(rx, json['instant_invite'])
                _invite = m.group(1)
                invite = await commands.InviteConverter().convert(ctx, _invite)
                assert isinstance(invite, discord.Invite)
                i = invite.uses if invite is not None else "No"
                embed = discord.Embed(title=json['name'])
                embed.add_field(name='Statistics',
                                value=f'Voice Channels: {len(json["channels"])}\n'
                                      f'Creation Date: {discord.utils.snowflake_time(int(json["id"]))}\n'
                                      f'Members: {len(json["members"])}\n'
                                      f'Invite: **{_invite}** #{invite.channel.name} ({invite.channel.id}), {i} Uses')
                return await ctx.send(embed=embed)
            elif json['data_type'] == 'guild_partial':
                return await ctx.send(f'Guild with ID {json["id"]} found, no other info found.')

    @commands.command()
    async def info(self, ctx, user: discord.User = None):
        """Gets information about a Discord user."""
        if user is None:
            user = ctx.author
        shared = str(len([i for i in ctx.bot.guilds if i.get_member(user.id)]))
        em = discord.Embed(title=f'Information for {user.display_name}:')
        em.add_field(name='Name:', value=user.name)
        em.add_field(name='Discriminator:', value=user.discriminator)
        em.add_field(name='ID:', value=user.id)
        em.add_field(name='Bot:', value=user.bot)
        em.add_field(name='Created At:', value=user.created_at)
        em.add_field(name='Shared Servers:', value=shared)
        em.set_thumbnail(url=user.avatar_url_as(static_format='png'))
        await ctx.send(embed=em)


def setup(bot: Bot):
    """Setup function for the cog"""
    bot.add_cog(Info(bot))
