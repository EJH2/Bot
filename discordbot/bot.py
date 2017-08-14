"""
Main bot file.
"""

import asyncio
import json
import sys
import traceback
from collections import Counter

import aiohttp
import asyncqlio.exc
import discord
from asyncqlio.db import DatabaseInterface
from discord.ext import commands
from discord.ext.commands import AutoShardedBot

from discordbot.cogs.utils import config, exceptions, formatter, tables
from discordbot.consts import init_modules, modules, bot_config


async def connect(user, password, db, host='localhost', port=5432):
    """
    Returns a Database object
    """
    url = f'postgresql://{user}:{password}@{host}:{port}/{db}'

    db = DatabaseInterface(url)
    await db.connect()

    return db


# noinspection PyUnresolvedReferences
class DiscordBot(AutoShardedBot):
    """
    Bot class.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bot_config = bot_config
        self.command_prefix_ = None
        self.db = None
        self.session = aiohttp.ClientSession(loop=self.loop, headers={"User-Agent": self.http.user_agent})

        # Set up logging
        discord_logger = formatter.setup_logger("discord")
        self.logger = formatter.setup_logger("Bot")
        self.command_logger = formatter.setup_logger("Commands")
        self.loggers = [discord_logger, self.logger, self.command_logger]

        self.logging = bot_config.get("logging", True)
        self.dynamic = bot_config.get("dynamicrules", True)

        self._loaded = False

        self.restarting = config.Config("restart.yaml")
        self.ignored = config.Config("ignored.yaml")

        self.owner = None
        self.owner_id = None

        self.pm_help = None

        # Dev mode
        self.debug = None

        self.commands_used = Counter()

        # As the great Danny once said: "pay no mind to this ugliness."
        self.remove_command("help")
        self.command(**self.help_attrs)(formatter.default_help_command)

        discord.abc.Messageable.send = formatter.send

        # Loads any modules that need loading before hand,
        # to do this name the file init_whatever.py in the cogs folder
        self.load_modules(init_modules, True)

    async def load_db(self):
        """
        Load DB for logging/dynamic rules.
        """
        if self.logging or self.dynamic:
            self.logger.info("Attempting to connect to DB...")
            creds = [bot_config["postgres"]["pg_user"], bot_config["postgres"]["pg_pass"], bot_config["postgres"][
                "pg_name"]]
            if "None" not in creds:
                try:
                    self.db = await connect(*creds)
                    self.logger.info("Connection established, database configured.")
                    msg = []
                    if self.logging:
                        msg.append("Logging")
                    if self.dynamic:
                        msg.append("Dynamic Rules")
                    self.logger.info(f"{'/'.join(msg)} enabled for this session.")
                except (asyncqlio.exc.DatabaseException, OSError) as e:
                    self.logging, self.dynamic = False, False
                    self.logger.warn("Could not connect to database: {}".format(e))
            else:
                self.logging, self.dynamic = False, False
                self.logger.warn("Could not connect to database.")
        else:
            self.logger.warn("Logging/dynamic rules disabled for this session.")
        if not self.logging:
            modules.remove("discordbot.cogs.logging")
        if not self.dynamic:
            modules.remove("discordbot.cogs.dynamic")
        if not self.db:
            modules.remove("discordbot.cogs.scheduling")

    async def get_prefix(self, message):
        bot_id = self.user.id
        prefixes = [f'<@!{bot_id}> ', f'<@{bot_id}> ', self.command_prefix_]
        if self.dynamic and self._loaded:
            if message.guild:
                async with self.db.get_session() as s:
                    query = await s.select(tables.Dynamic_Rules).where(
                        tables.Dynamic_Rules.guild_id == message.guild.id).first()
                if query:
                    attrs = json.loads(query.attrs)
                    if attrs.get("command_prefix"):
                        prefixes.append(attrs.get("command_prefix"))
        return prefixes

    def load_modules(self, modules_list: list, load_silent: bool = False):
        """
        Load bot extensions.
        """
        if len(modules_list) > 0:
            for mod in modules_list:
                try:
                    self.load_extension(mod)
                except Exception as e:
                    self.logger.critical(f"Could not load extension `{mod}` -> `{e}`")
                else:
                    if not load_silent:
                        self.logger.info(f"Loaded extension {mod}.")

    async def close(self):
        if not self.restarting.get('restarting', False):
            # Silence asyncqlio
            if self.db.connected:
                await self.db.close()
        for logger in self.loggers:
            logger.handlers = []
        await super().close()

    def __del__(self):
        if not self.restarting.get('restarting', False):
            # Silence aiohttp.
            if not self.http._session.closed:
                self.http._session.close()
            if not self.session.closed:
                self.session.close()

    async def on_ready(self):
        if self._loaded:
            return

        self.logger.info("Loaded Bot:")
        self.logger.info(f"Logged in as {self.user.name}#{self.user.discriminator}")
        self.logger.info("ID is {0.user.id}".format(self))
        self.description = f"Hello, this is the help menu for {self.user.name}!"

        self.logger.info("Downloading application info...")
        app_info = await self.application_info()
        self.owner = app_info.owner
        self.owner_id = app_info.owner.id
        self.logger.info(f"I am owned by {str(app_info.owner)}, setting owner.")

        # Set the playing statuses
        if self.shard_count > 1:
            for x in range(0, self.shard_count):
                await self.change_presence(game=discord.Game(name=f'Use {self.command_prefix_}help for help | Shard '
                                                                  f'{x + 1}/{self.shard_count}'), shard_id=x)
        else:
            await self.change_presence(game=discord.Game(name=f'Use {self.command_prefix_}help for help'))

        # Attempt to load the Postgres Database
        await self.load_db()

        # Attempt to load Bot modules
        self.load_modules(modules)

        if self.restarting.get("restarting"):
            await self.get_channel(int(self.restarting.get("restart_channel"))).send("Finished! Hello again ;)")
            self.restarting.delete("restarting")

        self._loaded = True

    async def on_member_join(self, member: discord.Member):
        """
        Gives a message when a user joins the server. It's opt-in though!
        """
        if self.dynamic and self._loaded:
            if member.guild:
                async with self.db.get_session() as s:
                    query = await s.select(tables.Dynamic_Rules).where(
                        tables.Dynamic_Rules.guild_id == member.guild.id).first()
                if query:
                    attrs = json.loads(query.attrs)
                    if attrs.get("announce_joins", False) == "True":
                        assert isinstance(member.guild, discord.Guild)
                        bot = discord.utils.get(member.guild.members, id=self.user.id)
                        for chan in member.guild.channels:
                            assert isinstance(chan, discord.abc.GuildChannel)
                            if chan.permissions_for(bot).send_messages is True:
                                await chan.send(f"Welcome, {member.mention}, to the server!")
                                break

    async def on_member_remove(self, member: discord.Member):
        """
        Gives a message when a user leaves the server. It's opt-in though!
        """
        if self.dynamic and self._loaded:
            if member.guild:
                async with self.db.get_session() as s:
                    query = await s.select(tables.Dynamic_Rules).where(
                        tables.Dynamic_Rules.guild_id == member.guild.id).first()
                if query:
                    attrs = json.loads(query.attrs)
                    if attrs.get("announce_leaves", False) == "True":
                        assert isinstance(member.guild, discord.Guild)
                        bot = discord.utils.get(member.guild.members, id=self.user.id)
                        for chan in member.guild.channels:
                            assert isinstance(chan, discord.abc.GuildChannel)
                            if chan.permissions_for(bot).send_messages is True:
                                await chan.send(f"Goodbye, {member.mention}!")
                                break

    async def on_message_edit(self, before, after):
        """
        Checks message edit to see if I screwed up a command...
        """
        await super().process_commands(after)

    async def on_command_error(self, ctx, e):
        """
        Catch command errors.
        """
        if isinstance(e, exceptions.Ignored):
            await ctx.channel.send("\N{CROSS MARK} This channel is currently being ignored.", delete_after=5)
        elif isinstance(e, commands.errors.NotOwner):
            await ctx.channel.send(f"\N{CROSS MARK} {e}", delete_after=5)
        elif isinstance(e, discord.errors.Forbidden):
            await ctx.channel.send("\N{NO ENTRY} I don't have permission to perform the action", delete_after=5)
        elif isinstance(e, exceptions.ClearanceError):
            await ctx.channel.send(f"\N{NO ENTRY} {e}", delete_after=5)
        elif isinstance(e, commands.errors.CommandNotFound):
            return
        elif isinstance(e, discord.errors.NotFound):
            return
        elif isinstance(e, exceptions.EmbedError):
            await ctx.channel.send("\N{NO ENTRY} This command requires the `Embed Links` "
                                   "permission to execute!", delete_after=5)
        elif isinstance(e, commands.errors.NoPrivateMessage):
            await ctx.channel.send("\N{NO ENTRY} That command can not be run in PMs!",
                                   delete_after=5)
            return
        elif isinstance(e, commands.errors.DisabledCommand):
            await ctx.channel.send("\N{NO ENTRY} Sorry, but that command is currently disabled!",
                                   delete_after=5)
        elif isinstance(e, commands.errors.CheckFailure):
            await ctx.channel.send("\N{CROSS MARK} Check failed. You probably don't have "
                                   "permission to do this.", delete_after=5)
        elif isinstance(e, commands.errors.CommandOnCooldown):
            await ctx.channel.send(f"\N{NO ENTRY} {e}", delete_after=5)
        elif isinstance(e, (commands.errors.BadArgument, commands.errors.MissingRequiredArgument)):
            await ctx.channel.send(f"\N{CROSS MARK} Bad argument: {' '.join(e.args)}", delete_after=5)
            formatted_help = await ctx.bot.formatter.format_help_for(ctx, ctx.command)
            for page in formatted_help:
                await ctx.channel.send(page, delete_after=20)
        else:
            await ctx.channel.send("\N{NO ENTRY} An error happened. This has been logged and reported.",
                                   delete_after=5)
            if isinstance(e, commands.errors.CommandInvokeError):
                traceback.print_exception(type(e), e.__cause__, e.__cause__.__traceback__, file=sys.stderr)
            else:
                traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)

    async def on_command(self, ctx):
        author = str(ctx.author)
        if ctx.guild is not None:
            self.command_logger.info(f"{ctx.guild.name} (ID: {ctx.guild.id}) > {author} (ID: {ctx.author.id}): "
                                     f"{ctx.message.clean_content}")
        else:
            self.command_logger.info(f"Private Messages > {author} (ID: {ctx.author.id}): {ctx.message.clean_content}")

    async def on_command_completion(self, ctx):
        self.commands_used[ctx.command.name] += 1
        await asyncio.sleep(5)
        try:
            await ctx.message.delete()
        except discord.DiscordException:
            pass

    def run(self):
        """
        Convenience function to run the bot with the specified token.
        """
        if self.debug:
            self.command_prefix = commands.when_mentioned_or(self.bot_config['bot'].get("dev_prefix",
                                                                                        self.bot_config['bot'][
                                                                                            'command_prefix']))
            token = self.bot_config['bot'].get('dev_token', self.bot_config['bot']['token'])
            self.command_prefix_ = self.bot_config['bot'].get("dev_prefix",
                                                              self.bot_config['bot']['command_prefix'])
        else:
            token = self.bot_config['bot']['token']
            self.command_prefix_ = self.bot_config['bot']['command_prefix']
        try:
            super().run(token)
        except discord.errors.LoginFailure as e:
            self.logger.error(f"Failed to login to discord: {e.args[0]}")
