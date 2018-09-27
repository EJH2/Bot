# coding=utf-8
"""
Modified command checks for the bot.
"""
from discord.ext import commands


class CheckError(commands.CheckFailure):
    def __init__(self, missing, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.missing = missing


class MissingPermission(CheckError):
    pass


class BotMissingPermission(CheckError):
    pass


class MissingRole(CheckError):
    pass


class BotMissingRole(CheckError):
    pass


async def check_permissions(ctx, perms, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    resolved = ctx.channel.permissions_for(ctx.author)
    result = check(getattr(resolved, name, None) == value for name, value in perms.items())
    if result is False:
        perms = list(name.replace('_', ' ').title() for name, _ in perms.items())
        raise MissingPermission(missing=perms)


async def bot_check_permissions(ctx, perms, *, check=all):
    resolved = ctx.channel.permissions_for(ctx.bot.user)
    result = check(getattr(resolved, name, None) == value for name, value in perms.items())
    if result is False:
        perms = list(name.replace('_', ' ').title() for name, _ in perms.items())
        raise BotMissingPermission(missing=perms)


def has_permissions(*, check=all, **perms):
    async def pred(ctx):
        return await check_permissions(ctx, perms, check=check)
    return commands.check(pred)


def bot_has_permissions(*, check=all, **perms):
    async def pred(ctx):
        return await check_permissions(ctx, perms, check=check)
    return commands.check(pred)


async def check_role(ctx, role):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    resolved = ctx.author.roles
    result = role.name.lower() in (r.name.lower() for r in resolved)
    if result is False:
        raise MissingRole(missing=role)


async def bot_check_role(ctx, role):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    resolved = ctx.author.roles
    result = role.name.lower() in (r.name.lower() for r in resolved)
    if result is False:
        raise BotMissingRole(missing=role)


def has_role(role):
    async def pred(ctx):
        return await check_role(ctx, role)
    return commands.check(pred)


def bot_has_role(role):
    async def pred(ctx):
        return await bot_check_role(ctx, role)
    return commands.check(pred)
