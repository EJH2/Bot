from discord.ext import commands
import asyncio
import discord
import json
from mods.utils.py import checks
import time
import os
import aiohttp
import sys
import logging
import pip
import io
import subprocess
import datetime
import re
from math import *
import traceback
import sqlite3

if os.path.isfile("mods/utils/json/configs/CarbonConfig.json"):
	with open("mods/utils/json/configs/CarbonConfig.json") as f:
		carbon = json.load(f)
if os.path.isfile("mods/utils/text/blacklist.txt"):
	pass
else:
	with open("mods/utils/text/blacklist.txt","a") as f:
		f.write("")
if os.path.isfile("mods/utils/text/channelblacklist.txt"):
	pass
else:
	with open("mods/utils/text/channelblacklist.txt","a") as f:
		f.write("")
if os.path.isfile("mods/utils/text/serverblacklist.txt"):
	pass
else:
	with open("mods/utils/text/serverblacklist.txt","a") as f:
		f.write("")
if os.path.isfile("mods/utils/logs/errors.txt"):
	pass
else:
	with open("mods/utils/logs/errors.txt","a") as f:
		f.write("")
with open("mods/utils/json/configs/config.json") as f:
	config = json.load(f)
with open("mods/utils/json/configs/credentials.json") as f:
	credentials = json.load(f)
with open("mods/utils/json/fun/hexnamestocode.json") as f:
	name = json.load(f)
with open("mods/utils/json/fun/hexcodestoname.json") as f:
	color = json.load(f)
description = ""
bot = commands.Bot(command_prefix=config["command_prefix"], description=description)
starttime = time.time()
starttime2 = time.ctime(int(time.time()))
bot.version = config["version"]
wrap = "```py\n{}\n```"
timestamp = time.strftime('%H:%M:%S')
bot.nicelogging = config["nicelogging"]

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)
log = logging.getLogger()
log.setLevel(logging.INFO)
handler = logging.FileHandler(filename='mods/utils/logs/discord.log', encoding='utf-8', mode='a')
log.addHandler(handler)

async def install(package):
	os.system("start /wait cmd /c pip install {}".format(package))
	await bot.say("Successfully installed `{}`".format(package))

async def uninstall(package):
	os.system("start /wait cmd /c 'pip uninstall {}'".format(package))
	await bot.say("Successfully uninstalled `{}`".format(package))

async def readfile(path):
	with open(path, mode="r") as f:
		if path[-5:] == ".json":
			resp = json.load(f)
		else:
			resp = []
			for i in f.readlines():
				resp.append(i[:18])
	await bot.say(resp)

installed_packages = pip.get_installed_distributions()
installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])
pip_list = "My currently installed pip packages are:\n" + "\n".join(map(str,installed_packages_list))

#CHAN = discord.get_channel(ID_HERE)
#await bot.send_message(CHAN, "something or other")

modules = [
	'mods.Moderation',
	'mods.Information',
	'mods.Fun',
	'mods.Internet'
]

async def dologging(message):
	conn = sqlite3.connect('ViralLog.db')
	cur = conn.cursor()
	cur.execute("CREATE TABLE IF NOT EXISTS LogTable(destination TEXT, author TEXT, time TEXT, content TEXT)")
	destination = None
	if message.channel.is_private:
		destination = 'Private Message'
	else:
		destination = '{0.server.name} > #{0.channel.name}'.format(message)
	content = message.clean_content.replace("\n",u"2063")
	cur.execute("INSERT INTO LogTable VALUES(destination, author, time, content)",(destination, message.author.name + "#" + message.author.discriminator, datetime.datetime.utcnow().strftime("%a %B %d %H:%M:%S %Y"),content))
	conn.commit()
	cur.close()
	conn.close()
	await bot.process_commands(message)

@bot.event
async def on_message(message):
	if "<@" + message.author.id + ">" in open('mods/utils/text/blacklist.txt').read() or message.author.bot == True:
		return
	elif message.server.id in open('mods/utils/text/serverblacklist.txt').read() or message.channel.id in open('mods/utils/text/channelblacklist.txt').read():
		if message.content.startswith(bot.command_prefix + "unignoreserv") or message.content.startswith(bot.command_prefix + "ignoreserv") or message.content.startswith(bot.command_prefix + "unignorechan") or message.content.startswith(bot.command_prefix + "ignorechan"):
			await dologging(message)
	else:		
		await dologging(message)

@bot.event
async def on_command_error(error,ctx):
	if isinstance(error,commands.NoPrivateMessage):
		await bot.send_message(ctx.message.author, "You can't use this command in private messages!")
	elif isinstance(error,commands.DisabledCommand):
		await bot.send_message(ctx.message.author, "Sorry, but that command you tried to use in #{} is disabled...".format(ctx.message.channel.name))
	elif isinstance(error,commands.CommandInvokeError):
		if bot.nicelogging == "True":
			with open("mods/utils/logs/errors.txt","a") as f:
				print('At {1}, {0.command.qualified_name} raised:'.format(ctx,datetime.datetime.utcnow().strftime("%a %B %d %H:%M:%S %Y")), file=f)
				traceback.print_tb(error.original.__traceback__,file=f)
				print('{0.__class__.__name__}: {0}'.format(error.original), file=f)
				print("\n\n==============\n\n",file=f)
			try:
				await bot.send_message(ctx.message.channel, wrap.format('{0.__class__.__name__}: {0}'.format(error.original)))
			except:
				try:
					await bot.send_message(ctx.message.author, "Hey! Around this time, you tried to activate a command. I couldn't complete it, so here's the error: {} When you get the chance, would you mind DMing EJH2 so he can fix it? He can be reached here: https://discord.gg/0xyhWAU4n2gQgYSF. Thanks!".format(wrap.format('{0.__class__.__name__}: {0}'.format(error.original))))
				except:
					print('In {0.command.qualified_name}:'.format(ctx), file=sys.stderr)
					traceback.print_tb(error.original.__traceback__)
					print('{0.__class__.__name__}: {0}'.format(error.original), file=sys.stderr)


@bot.event
async def on_ready():
	try:
		for extension in modules:
			try:
				bot.load_extension(extension)
			except Exception as e:
				print('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))
		bot.description = "This is the help menu for {}! Because of my extensive amount of commands (and my over-ambitious creator) I go on and offline a lot, so please bear with me! If you have any questions, just PM {}...".format(bot.user.name,carbon["ownername"])
		print('Logged in as')
		print(bot.user.name + "#" + bot.user.discriminator)
		print(bot.user.id)
		print('------')
	except Exception as e:
		print(type(e).__name__ + ': ' + str(e))

@bot.event
async def on_member_join(member):
	try:
		if config["dojoinleave"] == "True":
			print("hi")
			server = member.server
			fmt = 'Welcome {0.mention} to the server!'
			await bot.send_message(server, fmt.format(member))
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.event
async def on_member_remove(member):
	try:
		if config["dojoinleave"] == "True":
			print("bye")
			server = member.server
			fmt = '{0.mention} has left the server!'
			await bot.send_message(server, fmt.format(member))
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

class Default():
	def __init__(self,bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def info(self,ctx):
		"""Gives information about the bot."""
		try:
			await self.bot.say(bot.user.name + " was coded by EJH2 and Maxie!\nThe bot's version is `" + bot.version + "` and is running on Discord.py commands extension version `" + discord.__version__ + "`! It has seen `{}` users sending `{}` messages (since `{}` EST) in `{}` channels (including `{}` Private Channels) on a total of `{}` servers.".format(len(set(bot.get_all_members())), len(set(bot.messages)), starttime2.replace("  "," "), len(set(bot.get_all_channels())), len(set(bot.private_channels)), len(bot.servers)))
		except Exception as e:
			await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

	@commands.command(pass_context=True)
	async def uptime(self,ctx):
		"""Shows how long the bot has been online."""
		seconds = time.time() - starttime
		m, s = divmod(seconds, 60)
		h, m = divmod(m, 60)
		d, h = divmod(h, 24)
		w, d = divmod(d, 7)
		await self.bot.say("I have been online for %dw :" % (w) + " %dd :" % (d) + " %dh :" % (h) + " %dm :" % (m) + " %ds" % (s))

@bot.command(hidden=True)
@checks.is_owner()
async def load(*,module:str):
	"""Loads a part of the bot."""
	mod = "mods." + module
	if module == "all":
		for mod in modules:
			await bot.say("Alright, loading {}".format(mod))
			bot.load_extension(mod)
		await bot.say("Loading finished!")
	elif module in modules:
		await bot.say("Alright, loading {}".format(mod))
		bot.load_extension(mod)
		await bot.say("Loading finished!")
	else:
		await bot.say("You can't load a module that doesn't exist!")

@bot.command(hidden=True)
@checks.is_owner()
async def unload(*,module:str):
	"""Unloads a part of the bot."""
	mod = "mods." + module
	if module == "all":
		for mod in modules:
			await bot.say("Alright, unloading {}".format(mod))
			bot.unload_extension(mod)
			await bot.say("Done!")
		await bot.say("Unloading finished!")
	elif module in modules:
		await bot.say("Alright, unloading {}".format(mod))
		bot.unload_extension(mod)
		await bot.say("Unloading finished!")
	else:
		await bot.say("You can't unload a module that doesn't exist!")

@bot.command(hidden=True)
@checks.is_owner()
async def reload(*,module:str):
	"""Reloads a part of the bot."""
	mod = "mods." + module
	if module == "all":
		for mod in modules:
			await bot.say("Alright, reloading {}".format(mod))
			bot.unload_extension(mod)
			bot.load_extension(mod)
			await bot.say("Done!")
		await bot.say("Reloading finished!")
	elif mod in modules:
		await bot.say("Alright, reloading {}".format(mod))
		bot.unload_extension(mod)
		bot.load_extension(mod)
		await bot.say("Reloading finished!")
	else:
		await bot.say("You can't reload a module that doesn't exist!")


@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def debug(ctx,*,code:str):
	"""Evaluates code."""
	result = eval(code)
	if code.lower().startswith("print"):
		result
	elif asyncio.iscoroutine(result):
		await result
	else:
		await bot.say(wrap.format(result))

@bot.group(hidden=True,pass_context=True,invoke_without_command=True)
@checks.is_owner()
async def settings(ctx,setting,*,change):
	"""Changes bot variables."""
	if setting in config:
		with open("mods/utils/json/configs/config.json","r+") as f:
			ch = change.replace("<SPACE>", " ")
			config[setting] = ch
			f.seek(0)
			f.write(json.dumps(config))
			f.truncate()
			bot.__dict__[setting] = config[setting]
			await bot.say("Alright, I changed the setting `{}` to `{}`!".format(setting, ch))
	else:
		await bot.say("That isn't a valid setting!")

@settings.command(name="add",hidden=True,pass_context=True)
@checks.is_owner()
async def _add(ctx,setting,value):
	"""Adds bot variables."""
	if not setting in config:
		with open("mods/utils/json/configs/config.json","r+") as f:
			ch = value.replace("<SPACE>", " ")
			config[setting] = ch
			f.seek(0)
			f.write(json.dumps(config))
			f.truncate()
			bot.__dict__[setting] = config[setting]
			await bot.say("Alright, I added the setting `{}` with the value of `{}`!".format(setting, ch))
	else:
		await bot.say("There's already an existing setting named that!")

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def endbot(ctx):
	"""Kills the bot."""
	await bot.say("Shutting down...")
	await bot.logout()

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def restart(ctx):
	"""Restarts the bot."""
	await bot.say("Restarting...")
	await bot.logout()
	subprocess.call(["C:\\Python35\\python.exe","Clippy.py"])

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def setavatar(ctx,avatarlink:str):
	"""Sets the bots avatar."""
	path = "mods/utils/images/other/image.jpg"
	with aiohttp.ClientSession() as session:
		async with session.get(avatarlink) as resp:
			data = await resp.read()
			with open(path,"wb") as f:
				f.write(data)
	logo = open(path,"rb")
	await bot.edit_profile(avatar=logo.read())
	await bot.say("Avatar has successfully been changed!")

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def setname(ctx,*,name:str):
	"""Sets the bots name."""
	await bot.edit_profile(username=name)
	await bot.say("Username successfully changed to `{}`".format(name))

@bot.command(hidden=True,pass_contet=True)
@checks.is_owner()
async def setgame(*,game:discord.Game):
	"""Sets the game that ViralBot is playing."""
	await bot.change_status(game=game)
	await bot.say("Alright, changed ViralBot's current game to `{}`".format(game))

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def stream(ctx,game,url):
	await bot.change_status(game=discord.Game(url=url,type=1,name=game))
	await bot.say("I'm on the air!")

@bot.command(hidden=True,pass_contet=True)
@checks.is_owner()
async def cleargame():
	"""Clears the game status."""
	await bot.change_status(game=None)
	await bot.say("Alright, cleared ViralBot's game status.")

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def revert(ctx):
	"""Reverts the bots name and avatar back to its original."""
	await bot.edit_profile(username="ViralBot")
	logo = open("mods/utils/images/other/original.jpg","rb")
	asyncio.sleep(1)
	await bot.edit_profile(avatar=logo.read())
	await bot.say("ViralBot has successfully been reverted to its original!")

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def ignore(ctx,*users:discord.User):
	"""Blacklists a user from the bot."""
	for user in users:
		if user.id == "{}".format(config["ownerid"]):
			await bot.say("You can't blacklist the owner!")
		elif str(user.id) in open('mods/utils/text/blacklist.txt').read():
			await bot.say("{}#{} is already blacklisted!".format(user.name,user.discriminator))
		else:
			with open("mods/utils/text/blacklist.txt","a") as f:
				f.write(str(user.id) + "\n")
				await bot.say("Blacklisted {}#{}!".format(user.name,user.discriminator))

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def unignore(ctx,*users:discord.User):
	"""Unblacklists a user from the bot."""
	for user in users:
		if user.id == "{}".format(config["ownerid"]):
			await bot.say("You can't unblacklist the owner!")
		elif str(user.id) in open('mods/utils/text/blacklist.txt').read():
			with open('mods/utils/text/blacklist.txt') as f:
				newText=f.read().replace(user.id + "\n", '')
			with open('mods/utils/text/blacklist.txt', "w") as f:
				f.write(newText)
			await bot.say("Unblacklisted {}#{}".format(user.name,user.discriminator))
		else:
			await bot.say("{}#{} isn't blacklisted!".format(user.name,user.discriminator))

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def togglecmd(ctx,cmd:str):
	if cmd in bot.commands:
		cmd = bot.commands[cmd]
		if cmd.enabled == True:
			cmd.enabled = False
			await bot.say("The command `{}` is now disabled!".format(cmd))
		else:
			cmd.enabled = True
			await bot.say("The command `{}` is now enabled!".format(cmd))
	else:
		await bot.say("That isn't a valid command!")

bot.add_cog(Default(bot))

bot.run(credentials["token"])