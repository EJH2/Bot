"""
Main bot file.
"""

import asyncio
import logging
import sys
import traceback
from collections import Counter

import discord
import logbook
from discord.ext import commands
from discord.ext.commands import Bot
from logbook import Logger
from logbook import StreamHandler
from logbook.compat import redirect_logging

from discordbot.cogs.utils import config, exceptions
from discordbot.consts import modules, bot_config


class DiscordBot(Bot):
    """
    Bot class.
    """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.bot_config = bot_config

        # Set up logging
        redirect_logging()
        StreamHandler(sys.stderr).push_application()

        self.logger = Logger("Bot")
        self.logger.level = getattr(logbook, self.bot_config.get("log_level", "INFO"), logbook.INFO)

        # Set the root logger level, too.
        logging.root.setLevel(self.logger.level)

        self._loaded = False

        self.restarting = config.Config("restart.yaml")

        self.owner_id = None

        self.pm_help = True

        self.commands_used = Counter()

    def __del__(self):
        # Silence aiohttp.
        if not self.http.session.closed:
            self.http.session.close()

        if not self.session.closed:
            self.session.close()

    async def send_message(self, destination, content=None, *, tts=False, embed=None, delete_after=None):
        """
        Override for send_message that replaces `@everyone` with `@everyone` with a ZWSP.
        """
        content = str(content).replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")

        msg = await super().send_message(destination, content, tts=tts, embed=embed)

        if delete_after is not None:
            async def delete():
                await asyncio.sleep(delete_after)
                await self.delete_message(msg)

            discord.compat.create_task(delete(), loop=self.loop)

        return msg

    async def on_ready(self):
        if self._loaded:
            return

        self.logger.info("Loaded Bot:")
        self.logger.info("Logged in as {0.user.name}#{0.user.discriminator}".format(self))
        self.logger.info("ID is {0.user.id}".format(self))
        self.description = "Hello, this is the help menu for {0.user.name}!".format(self)

        self.logger.info("Downloading application info...")
        app_info = await self.application_info()
        self.owner_id = app_info.owner.id
        self.logger.info("I am owned by {}, setting owner.".format(str(app_info.owner)))

        # Attempt to load Bot modules
        for mod in modules:
            try:
                self.load_extension(mod)
            except Exception as e:
                self.logger.critical("Could not load extension `{}` -> `{}`".format(mod, e))
                self.logger.exception()
            else:
                self.logger.info("Loaded extension {}.".format(mod))

        if self.restarting.get("restarting"):
            await self.send_message(self.get_channel(str(self.restarting.get("restart_channel"))),
                                    "Finished! Hello again ;)")
            self.restarting.delete("restarting")

        self._loaded = True

    async def on_message(self, message):
        """
        Process commands and log.
        """
        self.logger.info("Received message: {message.clean_content} from {message.author.display_name}{bot}"
                         .format(message=message, bot=" [BOT]" if message.author.bot else ""))

        if message.server is not None:
            self.logger.info(" On channel: #{message.channel.name}".format(message=message))
            self.logger.info(" On server: {0.server.name} ({0.server.id})".format(message))
        else:
            self.logger.info(" Inside private message")

        await super().on_message(message)

    async def on_command_error(self, e, ctx):
        """
        Catch command errors.
        """
        if isinstance(e, (commands.errors.BadArgument, commands.errors.MissingRequiredArgument)):
            await self.send_message(ctx.message.channel,
                                    ":x: Bad argument: {}".format(" ".join(e.args)), delete_after=5)
        elif isinstance(e, exceptions.ClearanceError):
            await self.send_message(ctx.message.channel, e, delete_after=5)
            return
        elif isinstance(e, commands.errors.CheckFailure):
            await self.send_message(ctx.message.channel,
                                    ":x: Check failed. You probably don't have permission to do this.", delete_after=5)
            return
        elif isinstance(e, commands.errors.CommandNotFound):
            return
        elif isinstance(e, exceptions.Ignored):
            await self.send_message(ctx.message.channel, ":x: This channel is currently being ignored.", delete_after=5)
            return
        else:
            await self.send_message(ctx.message.channel,
                                    ":no_entry: An error happened. This has been logged and reported.", delete_after=5)
            if isinstance(e, commands.errors.CommandInvokeError):
                traceback.print_exception(type(e), e.__cause__, e.__cause__.__traceback__, file=sys.stderr)
            else:
                traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)

    async def on_command_completion(self, command, ctx):
        self.commands_used[command.name] += 1
        try:
            await self.delete_message(ctx.message)
        except Exception as e:
            print(e)

    def run(self):
        """
        Convenience function to run the bot with the specified token.
        """
        try:
            super().run(self.bot_config["bot"]["token"])
        except discord.errors.LoginFailure as e:
            self.logger.error("Failed to login to discord: {}".format(e.args[0]))
            sys.exit(2)
