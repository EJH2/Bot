"""
Bot runner.
"""
import asyncio
import os
import sys
import time

from discord.ext import commands

from discordbot.bot import DiscordBot
from discordbot.consts import bot_config, init_modules

kwargs = {"command_prefix": commands.when_mentioned_or(bot_config["bot"]["command_prefix"]), "description": "",
          "formatter": commands.HelpFormatter(show_check_failure=True)}


def init():
    # Initialising the bot instance, along with some helpful extras
    bot = DiscordBot(**kwargs)
    bot.filename = os.path.basename(__file__)
    bot.debug = any('debug' in arg.lower() for arg in sys.argv)

    return bot


def restart():
    bot = init()
    return bot


def main():
    bot = restart()
    if bot.debug:
        init_modules.remove("discordbot.cogs.init_stats")
    bot.run()
    while bot.restarting.get('restarting', False):
        print("Restarting in 5 seconds...", flush=True)
        time.sleep(5)
        print('Attempting to restart...\n'
              "-------------------"
              "\n")
        asyncio.set_event_loop(asyncio.new_event_loop())
        bot = restart()
        bot.run()
    return input("Press any key to continue...")


if __name__ == "__main__":
    main()
