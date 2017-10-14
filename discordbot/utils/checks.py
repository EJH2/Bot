"""
Checks for the bot.
"""
# TODO: Make this less ass

import discord
from discord.ext import commands

from discordbot.utils import exceptions


def is_server_owner(ctx):
    if ctx.bot.is_owner(ctx.author):
        return True
    if not ctx.guild:
        return True
    return ctx.author.id == ctx.guild.owner.id


def check_permissions(ctx, perms):
    if is_server_owner(ctx):
        return True
    ch = ctx.channel
    perm_list = ch.permissions_for(ctx.author)
    return any(getattr(perm_list, perm, None) == value for perm, value in perms.items())


def permissions(**perms):
    return lambda ctx: check_permissions(ctx, perms)


def check_bot_roles(ctx, role_names):
    if is_server_owner(ctx):
        return True
    ch = ctx.channel
    if not isinstance(ch, discord.abc.GuildChannel):
        return False
    me = ctx.guild.me
    role_list = list(map(lambda r: r.name.lower(), me.roles))
    _roles = any(name in role_list for name in role_names)
    if _roles:
        return True
    raise exceptions.ClearanceError(f"Bot requires role{'s' if len(role_names) > 1 else ''} \""
                                    f"{', '.join([role_name.title() for role_name in role_names])}\" to run that "
                                    f"command.")


def bot_roles(*role_names):
    return lambda ctx: check_bot_roles(ctx, role_names)


def check_user_roles(ctx, role_names):
    if is_server_owner(ctx):
        return True
    ch = ctx.channel
    if not isinstance(ch, discord.abc.GuildChannel):
        return False
    me = ctx.author
    role_list = list(map(lambda r: r.name.lower(), me.roles))
    _roles = any(name in role_list for name in role_names)
    if _roles:
        return True
    raise exceptions.ClearanceError(f"You need role{'s' if len(role_names) > 1 else ''} \""
                                    f"{', '.join([role_name.title() for role_name in role_names])}\" to run that "
                                    f"command.")


def user_roles(*role_names):
    return lambda ctx: check_user_roles(ctx, role_names)


def needs_embed(ctx):
    if not isinstance(ctx.channel, discord.abc.GuildChannel):
        return True
    if ctx.channel.permissions_for(ctx.guild.me).embed_links:
        return True
    raise exceptions.EmbedError


def needs_logging(ctx):
    if not ctx.bot.db:
        raise commands.errors.DisabledCommand
    return True
