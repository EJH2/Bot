# coding=utf-8
"""Main bot file"""
import aiohttp
import time
from collections import Counter, deque
from pathlib import Path

import discord
from discord.ext import commands
from pyppeteer import launch, errors

from bot.utils.logging import setup_logger
from bot.utils.over import send


discord.abc.Messageable.send = send


class Bot(commands.AutoShardedBot):
    """Subclasses AutoShardedBot to give more flexibility with design"""

    def __init__(self, *args, **kwargs):
        self.config = kwargs.pop('config')
        self.start_time = time.time()
        self.pm_help = None
        self.case_insensitive = True
        super().__init__(*args, **kwargs)
        self.app_info = None
        shard = f"| Shard {self.shard_id}" if self.shard_id else ""
        self.activity = discord.Game(name=f"{self.command_prefix}help {shard}")

        self.session = aiohttp.ClientSession(loop=self.loop, headers={"User-Agent": self.http.user_agent})
        self.browser_page = None
        self.browser = self.loop.create_task(self.create_browser())
        self.priv = self.config['extras'].get('privatebin', 'https://privatebin.net')
        self.polr = self.config['extras'].get('polr', None)

        self.commands_used = Counter()
        self.commands_used_in = Counter()
        self.errors = deque(maxlen=10)
        self.revisions = None

        discord_logger = setup_logger("discord")
        self.logger = setup_logger("Bot")
        self.command_logger = setup_logger("Commands")
        self.loggers = [discord_logger, self.logger, self.command_logger]

        _modules = [mod.stem for mod in Path("bot/cogs").glob("*.py")]
        self.load_extension(f"bot.cogs.core")
        self.load_extension(f"bot.cogs.owner")
        if 'bare' in kwargs.pop('argv'):  # load the bot bare-bones to diagnose issues
            return
        for module in _modules:
            try:
                if module in ['core', 'errors']:
                    pass
                self.load_extension(f"bot.cogs.{module}")
            except discord.DiscordException as exc:
                self.logger.error(f"{type(exc).__name__} occurred when loading {module}: {exc}")

        # make sure to only print ready text once
        self._loaded = False

    async def on_ready(self):
        """Function called when bot is ready or resumed"""
        if self._loaded is False:
            end_time = time.time() - self.start_time
            self.app_info = await self.application_info()
            self.logger.info(f"Loaded Bot:")
            self.logger.info(f"Logged in as {self.user}")
            self.logger.info(f"ID is {self.user.id}")
            self.logger.info(f"Owned by {self.app_info.owner}")
            self.description = f"Hello, this is the help menu for {self.user.name}!"
            self.logger.info(f"Bot started in {end_time} seconds")
            self._loaded = True
            return
        self.logger.info(f"Resumed bot session on shard {self.shard_id}!")

    async def create_browser(self):
        """Task to create browser for scraping purposes."""
        await self.wait_until_ready()
        self.browser = await launch(headless=True)
        self.browser_page = await self.browser.newPage()

    # noinspection PyProtectedMember
    async def close(self):
        """Function called when closing the bot"""
        try:
            await self.browser_page.close() or self.logger.info("Browser page successfully closed!")
        except errors.PageError:
            pass
        await self.browser.close() or self.logger.info("Browser successfully closed!")
        await super().close()
        await self.http._session.close()
        await self.session.close()
        for logger in self.loggers:
            for handler in logger.handlers:
                logger.removeHandler(handler)
