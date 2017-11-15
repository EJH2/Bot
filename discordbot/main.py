"""
Main bot file.
"""
import json
import time
from collections import Counter
from pathlib import Path

import aiohttp
import asyncpg
import asyncqlio
import discord
import nacl.secret
import nacl.utils
from discord.ext import commands
from ruamel import yaml

from discordbot.utils import db, formatter, tables


class DiscordBot(commands.AutoShardedBot):
    """Subclassing Bot allows for more unique handling of events in a
    controlled environment."""

    def __init__(self, *args, **kwargs):
        """
        Creates an instance of the bot.

        :param config_file: Configuration file to run the bot from.
        """
        super().__init__(*args, **kwargs)

        # Set up config file.
        self.config = {}

        with open("config.yaml") as config:
            self.config = yaml.safe_load(config)
        with open("cog_config.yaml") as c_config:
            self.cog_config = yaml.safe_load(c_config)

        # Setting up logging.
        discord_logger = formatter.setup_logger("discord")
        self.logger = formatter.setup_logger("Bot")
        self.command_logger = formatter.setup_logger("Commands")
        self.loggers = [discord_logger, self.logger, self.command_logger]

        # Setting up bot session.
        self.session = aiohttp.ClientSession(loop=self.loop, headers={"User-Agent": self.http.user_agent})

        # Configure cryptography for bot logging.
        if not self.config.get("crypt_key"):
            self.config["crypt_key"] = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
        self.cipher = nacl.secret.SecretBox(self.config.get("crypt_key"))

        # Placeholder items for later.
        self.command_prefix_ = self.config["bot"]["command_prefix"]
        self.db = None
        self.owner = None
        self.owner_id = None
        self._loaded = False
        self.ignored = {}

        # Debug mode for the bot.
        self.debug_mode = None

        # Commands related setup.
        self.commands_used = Counter()
        self.commands_used_in = Counter()

        # As the great Danny once said: "pay no mind to this ugliness."
        self.remove_command("help")
        self.command(**self.help_attrs)(formatter.default_help_command)

        discord.abc.Messageable.send = formatter.send

        # Module loading setup.
        self.modules = []
        init_modules = []

        for i in [x.stem for x in Path('discordbot/cogs').glob('*.py')]:
            mod = f"discordbot.cogs.{i}"
            init_modules.append(mod) if i.startswith("init_") else self.modules.append(mod)

        # Loads any modules that need loading before hand,
        # to do this name the file init_whatever.py in the cogs folder
        self.load_modules(init_modules, True)

        # Extras
        self.start_time = time.time()
        self.pm_help = None

    # Cleanup methods

    def __del__(self):
        # Silence aiohttp.
        if not self.http._session.closed:
            self.http._session.close()
        self.session.close()

    async def close(self):
        # Silence asyncqlio
        if self.db.connected:
            await self.db.close()
        for logger in self.loggers:
            logger.handlers = []
        await super().close()

    # Utility methods

    async def load_database(self):
        """
        Loads the database connection for the bot.

        :return: The database class.
        """
        credentials = [self.config["postgres"]["pg_user"], self.config["postgres"]["pg_pass"],
                       self.config["postgres"]["pg_name"]]
        if "None" in credentials:
            return None
        try:
            return await db.connect(*credentials)
        except (asyncqlio.DatabaseException, OSError) as e:
            self.logger.warn("Could not connect to database: {}".format(e))
            return None

    def load_modules(self, modules_list: list, load_silent: bool = False):
        """
        Loads the bot extensions.

        :param modules_list: List of the extensions that need loading.
        :param load_silent: Optionally disable console output while loading.
        :return: None
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

    # Bot methods

    async def get_prefix(self, message):
        bot_id = self.user.id
        prefixes = [f'<@!{bot_id}> ', f'<@{bot_id}> ', self.command_prefix_]
        if self.db and self._loaded and message.guild:
            try:
                async with self.db.get_session() as s:
                    query = await s.select(tables.Dynamic_Rules).where(
                        tables.Dynamic_Rules.guild_id == message.guild.id).first()
                if query:
                    attrs = json.loads(query.attrs)
                    if attrs.get("command_prefix"):
                        prefixes.append(attrs.get("command_prefix"))
            except asyncpg.exceptions.InterfaceError:
                pass
        return prefixes

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
        self.logger.info("Attempting to connect to database...")
        self.db = await self.load_database()
        if self.db:
            self.db.bind_tables(tables.Table)
            self.logger.info("Successfully connected to database!")
        else:
            self.logger.error("Unable to connect to database. Some bot features may not work correctly.")
            self.config["logging"], self.config["dynamic"] = None, None
            self.modules.remove("discordbot.cogs.scheduling")
        for cog in ["logging", "dynamicrules"]:
            if not self.config[cog]:
                self.modules.remove([c for c in self.modules if cog in c][0])

        # Load ignore list
        if self.db:
            async with self.db.get_session() as s:
                for type_ in ["users", "channels"]:
                    data_list = []
                    data = await (await s.select(tables.Ignored).where(tables.Ignored.type == type_[:-1]).all()
                                  ).flatten()
                    for entry in data:
                        data_list.append(entry.object_id)
                    self.ignored[type_] = data_list

        # Attempt to load Bot modules
        self.load_modules(self.modules)

        finished_time = time.time() - self.start_time

        self.logger.info(f"Finished loading! The bot took {finished_time} seconds to load.")
        self._loaded = True

    async def on_command_error(self, ctx, e):
        """
        "Catch" command errors until the handler cog has been loaded.
        """
        pass

    def run(self):
        """
        Convenience function to run the bot with the specified token.
        """
        bot_conf = self.config["bot"]
        c_p = bot_conf['command_prefix']
        token = bot_conf['token']
        if self.debug_mode:
            self.command_prefix = commands.when_mentioned_or(bot_conf.get("dev_prefix", c_p))
            token = bot_conf.get('dev_token', token)
            self.command_prefix_ = bot_conf.get("dev_prefix", c_p)
        try:
            super().run(token)
        except discord.errors.LoginFailure as e:
            self.logger.error(f"Failed to login to discord: {e.args[0]}")
