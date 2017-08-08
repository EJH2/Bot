"""
Formatting for various bot utilities.
"""

import logging
import re

import colorlog
import discord

from discordbot.cogs.utils import checks
from discordbot.consts import bot_config

# ===========================
#   Help related formatting
# ===========================

_mentions_transforms = {
    '@everyone': '@\u200beveryone',
    '@here': '@\u200bhere'
}

_mention_pattern = re.compile('|'.join(_mentions_transforms.keys()))


async def default_help_command(ctx, *commands: str):
    """
    Shows this message.
    """
    bot = ctx.bot
    destination = ctx.author if bot.pm_help else ctx.channel

    def repl(obj):
        return _mentions_transforms.get(obj.group(0), '')

    # help by itself just lists our own commands.
    if len(commands) == 0:
        pages = await bot.formatter.format_help_for(ctx, bot)
    elif len(commands) == 1:
        # try to see if it is a cog name
        name = _mention_pattern.sub(repl, commands[0])
        command = None
        if name in bot.cogs:
            command = bot.cogs[name]
        else:
            command = bot.all_commands.get(name)
            if command is None:
                await destination.send(bot.command_not_found.format(name))
                return

        pages = await bot.formatter.format_help_for(ctx, command)
    else:
        name = _mention_pattern.sub(repl, commands[0])
        command = bot.all_commands.get(name)
        if command is None:
            await destination.send(bot.command_not_found.format(name))
            return

        for key in commands[1:]:
            try:
                key = _mention_pattern.sub(repl, key)
                command = command.all_commands.get(key)
                if command is None:
                    await destination.send(bot.command_not_found.format(key))
                    return
            except AttributeError:
                await destination.send(bot.command_has_no_subcommands.format(command, key))
                return

        pages = await bot.formatter.format_help_for(ctx, command)

    if bot.pm_help is None:
        characters = sum(map(lambda l: len(l), pages))
        # modify destination based on length of pages.
        if characters > 1000:
            destination = ctx.author

    for page in pages:
        await destination.send(page)

    if destination == ctx.author:
        if isinstance(ctx.channel, discord.abc.PrivateChannel):
            pass
        else:
            embeddable = checks.needs_embed(ctx)
            if not embeddable:
                await ctx.channel.send("\N{ENVELOPE WITH DOWNWARDS ARROW ABOVE} Sent to your DMs!")
            else:
                em = discord.Embed(title="Sent!", description="\N{ENVELOPE WITH DOWNWARDS ARROW ABOVE} "
                                                              "Sent to your DMs!", color=0xFFFFFF)
                await ctx.channel.send(content="", embed=em)


# ==============================
#   Logging related formatting
# ==============================


def setup_logger(logger_name: str):
    """
    Setting up logging.
    """
    formatter = colorlog.LevelFormatter(
        fmt={
            "DEBUG": "{log_color}[{asctime}] [{name}] [{levelname}] {message}",
            "INFO": "{log_color}[{asctime}] [{name}] [{levelname}] {message}",
            "WARNING": "{log_color}[{asctime}] [{name}] [{levelname}] {message}",
            "ERROR": "{log_color}[{asctime}] [{name}] [{levelname}] {message}",
            "CRITICAL": "{log_color}[{asctime}] [{name}] [{levelname}] {message}",
        },
        log_colors={
            "DEBUG": "cyan",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red"
        },
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger(logger_name)
    logger.level = getattr(logging, bot_config.get("log_level", "INFO"), logging.INFO)

    # Set the root logger level, too.
    logging.root.setLevel(logger.level)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# ==============================
#   Message related formatting
# ==============================


old_send = discord.abc.Messageable.send


async def send(self, content=None, **kwargs):
    content = str(content).replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere") if content else None
    return await old_send(self, content, **kwargs)
