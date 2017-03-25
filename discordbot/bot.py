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
        self.ignored = config.Config("ignored.yaml")

        self.owner_id = None

        self.pm_help = True

        self.commands_used = Counter()

    def __del__(self):
        # Silence aiohttp.
        if not self.http.session.closed:
            self.http.session.close()

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
            await self.get_channel(int(self.restarting.get("restart_channel"))).send("Finished! Hello again ;)")
            self.restarting.delete("restarting")

        self._loaded = True

    async def on_message(self, message):
        """
        Process commands and log.
        """
        if message.channel.id not in self.ignored.get("channels"):
            if message.attachments:
                if message.clean_content:
                    attachment = " " + message.attachments[0]["url"]
                else:
                    attachment = message.attachments[0]["url"]
            else:
                attachment = ""

            self.logger.info("Received message: {message.clean_content}{attachment}".format(message=message,
                                                                                            attachment=attachment))
            self.logger.info(" From user: {message.author.display_name}{bot} ({message.author.id})"
                             .format(message=message, bot=" [BOT]" if message.author.bot else ""))

            if message.guild is not None:
                self.logger.info(" In channel: #{message.channel.name}".format(message=message))
                self.logger.info(" In server: {0.guild.name} ({0.guild.id})".format(message))
            else:
                self.logger.info(" Inside private message")

        await super().on_message(message)

    async def on_message_edit(self, before, after):
        """
        Checks message edit to see if I screwed up a command...
        """
        await super().on_message(after)

    async def on_command_error(self, e, ctx):
        """
        Catch command errors.
        """
        if isinstance(e, (commands.errors.BadArgument, commands.errors.MissingRequiredArgument)):
            await ctx.message.channel.send("\N{CROSS MARK} Bad argument: {}".format(" ".join(e.args)), delete_after=5)
        elif isinstance(e, exceptions.ClearanceError):
            await ctx.message.channel.send(e, delete_after=5)
            return
        elif isinstance(e, commands.errors.CheckFailure):
            await ctx.message.channel.send("\N{CROSS MARK} Check failed. You probably don't have permission to do this."
                                           , delete_after=5)
            return
        elif isinstance(e, commands.errors.CommandNotFound):
            return
        elif isinstance(e, exceptions.EmbedError):
            await ctx.message.channel.send("\N{NO ENTRY} This command requires the `Embed Links` permission to execute!"
                                           , delete_after=5)
            return
        elif isinstance(e, exceptions.Ignored):
            await ctx.message.channel.send("\N{CROSS MARK} This channel is currently being ignored.", delete_after=5)
            return
        else:
            await ctx.message.channel.send("\N{NO ENTRY} An error happened. This has been logged and reported.",
                                           delete_after=5)
            if isinstance(e, commands.errors.CommandInvokeError):
                traceback.print_exception(type(e), e.__cause__, e.__cause__.__traceback__, file=sys.stderr)
            else:
                traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)

    @staticmethod
    async def on_command(ctx):
        embeddable = ctx.message.channel.permissions_for(ctx.message.guild.me).embed_links
        if ctx.command.name == "help":
            if not embeddable:
                await ctx.message.channel.send("\N{ENVELOPE WITH DOWNWARDS ARROW ABOVE} Sent to your DMs!")
            else:
                em = discord.Embed(title="Sent!", description="\N{ENVELOPE WITH DOWNWARDS ARROW ABOVE} "
                                                              "Sent to your DMs!", color=0xFFFFFF)
                await ctx.message.channel.send(content="", embed=em)

    async def on_command_completion(self, ctx):
        self.commands_used[ctx.command.name] += 1
        await asyncio.sleep(5)
        try:
            await ctx.message.delete()
        except Exception as e:
            print(e)

    def _run(self):
        """
        Convenience function to run the bot with the specified token.
        """
        try:
            super().run(self.bot_config["bot"]["token"])
        except discord.errors.LoginFailure as e:
            self.logger.error("Failed to login to discord: {}".format(e.args[0]))

    def run(self):
        """
        Extra cleanup for _run.
        """
        self._run()
        input("Press any key to continue...")
        sys.exit(2)
