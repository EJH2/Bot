from discord.ext import commands
from discord.errors import *
import asyncio
import discord
import logging
import checks
import json
import os

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)
log = logging.getLogger()
log.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
log.addHandler(handler)

with open("config.json") as f:
    config = json.load(f)
description = '''This is the help menu for Clip.py'''
bot = commands.Bot(command_prefix=config["command_prefix"], description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print("The disabled version of " + bot.user.name)
    print(bot.user.id)
    print('------')

class Enable():
    def __init__(self,bot):
        self.bot = bot

    @commands.command(name="enable",hidden=True,pass_context=True)
    @checks.is_owner()
    async def cmd_enable(self,ctx):
        try:
            await self.bot.say("Re-Enabling...")
            os.system("ClippyNew.py")
        except Exception as e:
            print(type(e).__name__ + ': ' + str(e))

bot.add_cog(Enable(bot))

bot.run("clip.py@mail.com", "7536970e")