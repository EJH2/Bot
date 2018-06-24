# coding=utf-8
"""Main bot file"""
import asyncio
import datetime
import os

import aiohttp
import time
from collections import Counter
from pathlib import Path

import discord
import git
import humanize
from discord import DiscordException
from discord.ext import commands

from bot.utils.logging import setup_logger
from bot.utils.over import send


discord.abc.Messageable.send = send


class Bot(commands.AutoShardedBot):
    """Subclasses AutoShardedBot to give more flexibility with design"""

    def __init__(self, *args, **kwargs):
        self.config = kwargs.pop('config')
        self._start_time = time.time()
        self.app_info = None
        self.case_insensitive = True
        super().__init__(*args, **kwargs)
        shard = f"| Shard {self.shard_id}" if self.shard_id else ""
        self.activity = discord.Game(name=f"{self.command_prefix}help {shard}")
        self.session = aiohttp.ClientSession(loop=self.loop, headers={"User-Agent": self.http.user_agent})
        self.commands_used = Counter()
        self.commands_used_in = Counter()
        self.revision_loop = self.loop.create_task(self.get_revisions())
        self.revisions = None

        discord_logger = setup_logger("discord")
        self.logger = setup_logger("Bot")
        self.command_logger = setup_logger("Commands")
        self.loggers = [discord_logger, self.logger, self.command_logger]

        _modules = [mod.stem for mod in Path("bot/cogs").glob("*.py")]
        self.load_extension(f"bot.cogs.core")
        self.load_extension(f"bot.cogs.errors")
        if 'bare' in kwargs.pop('argv'):  # load the bot bare-bones to diagnose issues
            return
        for module in _modules:
            try:
                if module in ['core', 'errors']:
                    pass
                self.load_extension(f"bot.cogs.{module}")
            except DiscordException as exc:
                self.logger.error(f"{type(exc).__name__} occurred when loading {module}: {exc}")

        # make sure to only print ready text once
        self._loaded = False

    async def get_revisions(self):
        """_get_revisions but for a looped task"""
        await self.wait_until_ready()
        while not self.is_closed():
            await self._get_revisions()
            await asyncio.sleep(3600)

    async def _get_revisions(self):
        """Get latest git revisions"""
        repo = git.Repo(os.getcwd())
        url = repo.remote().urls.__next__()
        commit_url = url.split("@")[1].replace(":", "/")[:-4]
        commits = []
        unpublished_commits = list(repo.iter_commits('master@{u}..master'))
        for commit in list(repo.iter_commits("master"))[:3]:
            commit_time = humanize.naturaltime(datetime.datetime.now(tz=commit.committed_datetime.tzinfo)
                                               - commit.committed_datetime)
            if commit not in unpublished_commits:
                commits.append(f"[`{commit.hexsha[:7]}`](https://{commit_url}/commit/{commit.hexsha[:7]}) "
                               f"{commit.summary} ({commit_time})")
            else:
                commits.append(f"`{commit.hexsha[:7]}` {commit.summary} ({commit_time})")
        self.revisions = '\n'.join(commits)

    async def on_ready(self):
        """Function called when bot is ready or resumed"""
        if self._loaded is False:
            end_time = time.time() - self._start_time
            self.app_info = await self.application_info()
            self.owner_id = self.app_info.owner.id
            self.logger.info(f"Loaded Bot:")
            self.logger.info(f"Logged in as {self.user}")
            self.logger.info(f"ID is {self.user.id}")
            self.logger.info(f"Owned by {self.app_info.owner}")
            self.description = f"Hello, this is the help menu for {self.user.name}!"
            self.logger.info(f"Bot started in {end_time} seconds")
            self._loaded = True
            return
        self.logger.info(f"Resumed bot session on shard {self.shard_id}!")

    async def close(self):
        """Function called when closing the bot"""
        await super().close()
        for logger in self.loggers:
            for handler in logger:
                logger.removeHandler(handler)
        await self.http._session.close()
        await self.session.close()
