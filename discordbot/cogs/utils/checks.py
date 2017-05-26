"""
Checks.
"""

import discord

from discordbot.cogs.utils import exceptions


def is_owner(ctx):
    owner_id = ctx.bot.owner_id
    return ctx.message.author.id == owner_id


def is_server_owner(ctx):
    if is_owner(ctx):
        return True
    return ctx.message.author.id == ctx.message.guild.owner.id


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
    raise exceptions.ClearanceError("Bot requires role{} \"{}\" to run that command.".format("s" if len(role_names) > 1
                                                                                             else "", ", ".join(
        [role_name.title() for role_name in role_names])))


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
    raise exceptions.ClearanceError("You need role{} \"{}\" to run that command.".format("s" if len(role_names) > 1
                                                                                         else "", ", ".join(
        [role_name.title() for role_name in role_names])))


def user_roles(*role_names):
    return lambda ctx: check_user_roles(ctx, role_names)


def needs_embed(ctx):
    if not isinstance(ctx.channel, discord.abc.GuildChannel):
        return True
    if ctx.message.channel.permissions_for(ctx.message.guild.me).embed_links:
        return True
    raise exceptions.EmbedError
