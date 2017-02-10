"""
Checks.
"""

from discord.ext import commands

from discordbot.cogs.utils import exceptions


def is_owner(ctx):
    owner_id = ctx.bot.owner_id
    return ctx.message.author.id == owner_id


def is_server_owner(ctx):
    if is_owner:
        return True
    return ctx.message.author.id == ctx.message.guild.owner.id


def check_permissions(ctx, perms):
    if is_server_owner:
        return True
    ch = ctx.message.channel
    author = ctx.message.author
    resolved = ch.permissions_for(author)
    return all(getattr(resolved, name, None) == value for name, value in perms.items())


def permissions(**perms):
    return lambda ctx: check_permissions(ctx, perms)


def role(role_name):
    def predicate(ctx):
        if is_server_owner:
            return True
        if ctx.message.guild:
            for role in ctx.message.guild.me.roles:
                if role.name.lower() == role_name.lower():
                    return True
        raise exceptions.ClearanceError("Bot requires role \"{}\" to run that command.".format(role_name.title()))

    return commands.check(predicate)


def needs_embed(ctx):
    if ctx.message.channel.permissions_for(ctx.message.guild.me).embed_links:
        return True
    raise exceptions.EmbedError
