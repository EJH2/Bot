"""
Bot start-up script.
"""
import sys

from discord.ext import commands
from ruamel import yaml

from discordbot.main import DiscordBot

with open("config.yaml") as config:
    config = yaml.safe_load(config)

kwargs = {"command_prefix": commands.when_mentioned_or(config["bot"]["command_prefix"]), "description": "",
          "formatter": commands.HelpFormatter(show_check_failure=True)}

discord_bot = DiscordBot(**kwargs)
discord_bot.debug_mode = any('debug' in arg.lower() for arg in sys.argv)
discord_bot.run()
input("Press any key to continue...")
