"""
Formatting for various bot utilities.
"""

import datetime
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
    destination = ctx.message.author if bot.pm_help else ctx.message.channel

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
            destination = ctx.message.author

    for page in pages:
        await destination.send(page)

    if destination == ctx.message.author:
        if isinstance(ctx.message.channel, discord.abc.PrivateChannel):
            pass
        else:
            embeddable = checks.needs_embed(ctx)
            if not embeddable:
                await ctx.message.channel.send("\N{ENVELOPE WITH DOWNWARDS ARROW ABOVE} Sent to your DMs!")
            else:
                em = discord.Embed(title="Sent!", description="\N{ENVELOPE WITH DOWNWARDS ARROW ABOVE} "
                                                              "Sent to your DMs!", color=0xFFFFFF)
                await ctx.message.channel.send(content="", embed=em)


# ==============================
#   Logging related formatting
# ==============================


def setup_logger(logger_name: str):
    """
    Setting up logging.
    """
    datefmt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    formatter = colorlog.LevelFormatter(
        fmt={
            "DEBUG": "{log_color}[" + datefmt + "] [{name}] [{levelname}] {message}",
            "INFO": "{log_color}[" + datefmt + "] [{name}] [{levelname}] {message}",
            "WARNING": "{log_color}[" + datefmt + "] [{name}] [{levelname}] {message}",
            "ERROR": "{log_color}[" + datefmt + "] [{name}] [{levelname}] {message}",
            "CRITICAL": "{log_color}[" + datefmt + "] [{name}] [{levelname}] {message}"
        },
        log_colors={
            "DEBUG": "cyan",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red"
        },
        style="{",
        datefmt=""
    )
    logger = logging.getLogger(logger_name)
    logger.level = getattr(logging, bot_config.get("log_level", "INFO"), logging.INFO)

    # Set the root logger level, too.
    logging.root.setLevel(logger.level)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def file_logger(path):
    """
    File logging™.
    """
    log = logging.getLogger("Messages")
    log.handlers = []
    handler = logging.FileHandler(filename=path, encoding='utf-8', mode='a')
    log.addHandler(handler)

    return log


# ==============================
#   Message related formatting
# ==============================


old_send = discord.abc.Messageable.send


async def new_send(self, content, **kwargs):
    content = content.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
    return await old_send(self, content, **kwargs)
