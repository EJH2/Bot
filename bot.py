#!/usr/bin/env python
"""
Bot runner.
"""

import os
import sys

from discord.ext.commands import when_mentioned_or

from discordbot.bot import DiscordBot
from discordbot.consts import bot_config, init_modules

if __name__ == "__main__":
    bot = DiscordBot(command_prefix=when_mentioned_or(bot_config["bot"]["command_prefix"]), description="")
    bot.filename = os.path.basename(__file__)
    bot.debug = any('debug' in arg.lower() for arg in sys.argv)
    if bot.debug:
        init_modules.remove("discordbot.cogs.init_stats")
    bot.run()
    input("Press any key to continue...")
    sys.exit(2)
