import asyncio
import glob
import os
import shutil
import sys
import time

from ruamel import yaml

from discordbot.cogs.utils import util

# Creating a bot_config file path
config_file = os.path.join(os.getcwd(), "config.yaml")


# Attempting to download anc clone if not found
async def download_config():
    print("It appears that you do not have an existing bot config file! Attempting to clone one...", file=sys.stderr)
    try:
        shutil.copy("config.example.yaml", "config.yaml")
        print("Created a new bot config file - please fill out the required fields and restart the bot.")
        input("Press any key to continue...")
        sys.exit(1)
    except FileNotFoundError:
        print("It seems that you did not download the example bot config file! Downloading and copying...")
        try:
            await util.download("https://github.com/EJH2/ViralBot/blob/master/config.example.yaml",
                                "config.example.yaml")
        except util.Borked:
            print("Config could not be cloned automatically, please ask on GitHub or Discord", file=sys.stderr)
            input("Press any key to continue...")
            sys.exit(1)
        print("Cloning...")
        shutil.copy("config.example.yaml", "config.yaml")
        print("Created a new bot config file - please fill out the required fields and restart the bot.")
        input("Press any key to continue...")
        sys.exit(1)


# Run asynchronously
if not os.path.exists(config_file):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(download_config())

with open(config_file) as f:
    bot_config = yaml.safe_load(f)

# Bot Up-time Calculation things
start2 = time.ctime(int(time.time()))

start = time.time()

# Bot Module Loading things
modules = []
init_modules = []

for i in glob.glob(os.getcwd() + "/discordbot/cogs/*.py"):
    if "init" in i:
        init_modules.append(i.replace(os.getcwd() + "/", "").replace("\\", ".").replace("/", ".")[:-3])
    else:
        modules.append(i.replace(os.getcwd() + "/", "").replace("\\", ".").replace("/", ".")[:-3])
