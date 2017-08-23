"""
Bot runner.
"""
import asyncio
import importlib
import os
import sys
import time

from discord.ext import commands

from discordbot import bot
from discordbot.consts import bot_config, init_modules

kwargs = {"command_prefix": commands.when_mentioned_or(bot_config["bot"]["command_prefix"]), "description": "",
          "formatter": commands.HelpFormatter(show_check_failure=True)}

# Make it so the uptime reflects restarts as well
start = time.time()


# Initialising the bot instance, along with some helpful extras
def init():
    importlib.reload(bot)  # This will make sure we reload *all* of the bot, and not just the cogs
    discord_bot = bot.DiscordBot(**kwargs)
    discord_bot.filename = os.path.basename(__file__)
    discord_bot.start_time = start
    discord_bot.debug = any('debug' in arg.lower() for arg in sys.argv)

    return discord_bot


def restart():
    discord_bot = init()
    discord_bot.restarting.delete("restarting")
    return discord_bot


def main():
    discord_bot = restart()
    if discord_bot.debug:
        init_modules.remove("discordbot.cogs.init_stats")
    discord_bot.run()
    while discord_bot.restarting.get('restarting', False):
        print("Restarting in 5 seconds...", flush=True)
        time.sleep(5)
        print('Attempting to restart...\n'
              "-------------------"
              "\n")
        asyncio.set_event_loop(asyncio.new_event_loop())
        discord_bot = restart()
        discord_bot.run()
    return input("Press any key to continue...")


if __name__ == "__main__":
    main()
