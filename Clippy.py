from discord.ext import commands
import asyncio
import discord
import json
from mods.utils import checks
import time
import os
import aiohttp
import sys
import logging
import pip

with open("mods/utils/config.json") as f:
	config = json.load(f)
with open("mods/utils/credentials.json") as f:
	credentials = json.load(f)
with open("mods/utils/hexnamestocode.json") as f:
	name = json.load(f)
with open("mods/utils/hexcodestoname.json") as f:
	color = json.load(f)
description = "This is the help menu for Clip.py! Because of my extensive amount of commands (and my over-ambitious creator) I go on and offline a lot, so please bear with me! If you have any questions, just PM EJH2#0674..."
bot = commands.Bot(command_prefix=config["command_prefix"], description=description)
starttime = time.time()
starttime2 = time.ctime(int(time.time()))
bot.version = config["version"]
wrap = "```py\n{}\n```"
bot.pm_help = True

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='mods/utils/discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

async def install(package):
	if "--upgrade" in package:
		await bot.say("You can't use --upgrade!")
	else:
		pip.main(['install', package])
		return "Successfully installed {}".format(package)

def uninstall(package):
	pip.main(['uninstall', package])
	return "Successfully uninstalled {}".format(package)

installed_packages = pip.get_installed_distributions()
installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
     for i in installed_packages])
pip_list = "My currently installed pip packages are:\n" + "\n".join(map(str,installed_packages_list))

#CHAN = discord.get_channel(ID_HERE)
#await bot.send_message(CHAN, "something or other")

modules = [
	'mods.Moderation',
	'mods.Information',
	'mods.Fun'
]

@bot.event
async def on_message(message):
	if os.path.isfile("mods/utils/blacklist.txt"):
		pass
	else:
		with open("mods/utils/blacklist.txt","a") as f:
			f.write("")
	if "<@" + message.author.id + ">" in open('mods/utils/blacklist.txt').read():
		return
	await bot.process_commands(message)

@bot.event
async def on_ready():
	for extension in modules:
		try:
			bot.load_extension(extension)
		except Exception as e:
			print('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))
	print('Logged in as')
	print(bot.user.name + "#" + bot.user.discriminator)
	print(bot.user.id)
	print('------')

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
			await self.bot.say(bot.user.name + " was coded by EJH2 and Maxie!\nThe bot's version is `" + bot.version + "` and is running on Discord.py commands extension version `" + discord.__version__ + "`! It has seen `{}` users sending `{}` messages (since `{}` EST) in `{}` channels (including `{}` Private Channels) on a total of `{}` servers.".format(len(set(bot.get_all_members())), len(set(bot.messages)), starttime2, len(set(bot.get_all_channels())), len(set(bot.private_channels)), len(bot.servers)))
		except Exception as e:
			await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

	@commands.command(pass_context=True)
	async def uptime(self,ctx):
		"""Shows how long the bot has been online."""
		try:
			seconds = time.time() - starttime
			m, s = divmod(seconds, 60)
			h, m = divmod(m, 60)
			d, h = divmod(h, 24)
			w, d = divmod(d, 7)
			await self.bot.say("I have been online for %dw :" % (w) + " %dd :" % (d) + " %dh :" % (h) + " %dm :" % (m) + " %ds" % (s))
		except Exception as e:
			await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.command(hidden=True)
@checks.is_owner()
async def load(*,module:str):
	"""Loads a part of the bot."""
	module = "mods." + module
	try:
		if module in modules:
			await bot.say("Alright, loading {}".format(module))
			bot.load_extension(module)
			await bot.say("Loading finished!")
		else:
			await bot.say("You can't load a module that doesn't exist!")
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.command(hidden=True)
@checks.is_owner()
async def unload(*,module:str):
	"""Unloads a part of the bot."""
	module = "mods." + module
	try:
		if module in modules:
			await bot.say("Alright, unloading {}".format(module))
			bot.unload_extension(module)
			await bot.say("Unloading finished!")
		else:
			await bot.say("You can't unload a module that doesn't exist!")
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.command(hidden=True)
@checks.is_owner()
async def reload(*,module:str):
	"""Reloads a part of the bot."""
	mod = "mods." + module
	try:
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
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def debug(ctx,*,code:str):
	"""Evaluates code."""
	try:
		result = eval(code)
		if code.lower().startswith("print"):
			result
		elif asyncio.iscoroutine(result):
			await result
		else:
			await bot.say(wrap.format(result))
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def settings(ctx,setting,*,change):
	"""Changes bot variables."""
	try:
		if setting in config:
			ch = change.replace("<SPACE>", " ")
			config[setting] = ch
			f.seek(0)
			f.write(json.dumps(config))
			f.truncate()
			bot.__dict__[setting] = config[setting]
			await bot.say("Alright, I changed the setting `{}` to `{}`!".format(setting, ch))
		else:
			await bot.say("That isn't a valid setting!")
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def endbot(ctx):
	"""Kills the bot."""
	try:
		await bot.say("Shutting down...")
		await bot.logout()
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def restart(ctx):
	"""Restarts the bot."""
	try:
		await bot.say("Restarting...")
		os.system("Clippy.py")
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def setavatar(ctx,avatarlink:str):
	"""Sets the bots avatar."""
	try:
		path = "mods/utils/image.jpg"
		with aiohttp.ClientSession() as session:
			async with session.get(avatarlink) as resp:
				data = await resp.read()
				with open(path,"wb") as f:
					f.write(data)
		logo = open(path,"rb")
		await bot.edit_profile(avatar=logo.read())
		await bot.say("Avatar has successfully been changed!")
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def setname(*,name:str):
	"""Sets the bots name."""
	try:
		await bot.edit_profile(username=name)
		await bot.say("Username successfully changed to `{}`".format(name))
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.command(pass_contet=True)
@checks.is_owner()
async def setgame(*,game:discord.Game):
	"""Sets the game that Clip.py is playing."""
	try:
		await bot.change_status(game=game)
		await bot.say("Alright, changed Clip.py's current game to `{}`".format(game))
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.command(pass_contet=True)
@checks.is_owner()
async def cleargame():
	"""Sets the game that Clip.py is playing."""
	try:
		await bot.change_status(game=None)
		await bot.say("Alright, cleared Clip.py's game status.")
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def revert(ctx):
	"""Reverts the bots name and avatar back to its original."""
	try:
		await bot.edit_profile(username="Clip.py")
		logo = open("mods/utils/original.jpg","rb")
		await bot.edit_profile(avatar=logo.read())
		await bot.say("Clip.py has successfully been reverted to its original!")
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def blacklist(ctx,user:str):
	"""Blacklists a user from the bot."""
	try:
		if user == "<{}>".format(config["ownerid"]):
			await bot.say("You can't blacklist the owner!")
		elif user in open('mods/utils/blacklist.txt').read():
			await bot.say("That user is already blacklisted!")
		else:
			with open("mods/utils/blacklist.txt","a") as f:
				f.write(user + "\n")
				await bot.say("Blacklisted that user!")
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

@bot.command(hidden=True,pass_context=True)
@checks.is_owner()
async def unblacklist(ctx,user:str):
	"""Unblacklists a user from the bot."""
	try:
		if len(set(ctx.message.mentions)) > 0:
			if user == "<{}>".format(config["ownerid"]):
				await bot.say("You can't unblacklist the owner!")
			elif user in open('mods/utils/blacklist.txt').read():
				fin = open('mods/utils/blacklist.txt', 'r')
				fout = open('mods/utils/blacklist.txt', 'w')
				for line in fin:
					for word in delete_list:
						line = line.replace(word, "")
					fout.write(line)
				fin.close()
				fout.close()
				await bot.say("Unblacklisted that user!")
			else:
				await bot.say("That user isn't blacklisted!")
		else:
			await bot.say("You have to mention someone!")
	except Exception as e:
		await bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

bot.add_cog(Default(bot))

bot.run(credentials["token"])