# coding=utf-8
"""Main bot file."""

import os
import sys

from ruamel import yaml

from bot import main
from bot.utils.over import HelpFormatter

if not sys.version_info >= (3, 6):
    raise RuntimeError("Python 3.6+ not detected! Please run with 3.6 or above.")

path = os.getcwd()

debug = "debug" in sys.argv

with open(f"{path}/{'dev_' if debug else ''}config.yaml") as _config:
    config = yaml.round_trip_load(_config)

bot = main.Bot(command_prefix=config["bot"]["prefix"], config=config, argv=sys.argv, formatter=HelpFormatter())

if __name__ == "__main__":
    bot.run(config["bot"]["token"])
