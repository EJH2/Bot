import time
import asyncio
from discord.ext import commands
import discord.utils
import pyowm
import json
from discord.errors import *
import requests
import aiohttp

with open("mods/utils/config.json") as f:
	config = json.load(f)

wrap = "```py\n{0}\n```"
xl = "```xl\n{0}\n```"

class Information():
	def __init__(self,bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def ping(self,ctx):
		"""Pings the bot."""
		try:
			pingtime = time.time()
			pingmsg = await self.bot.say("Pinging Server...")
			ping = time.time() - pingtime
			await self.bot.edit_message(pingmsg, "It took %.01f" % (ping) + " seconds to ping the server!")
		except Exception as e:
			await self.bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

	@commands.command(pass_context=True)
	async def playerinfo(self,ctx,*users:discord.User):
		"""Gives you player info on a user."""
		try:
			if not users:
				targetMember = ctx.message.author
				server = ctx.message.server
				seeinserver = str(len(set([member.server.name for member in self.bot.get_all_members() if member.name == targetMember.name])))
				x = 'Your Player Information:\nUsername: "{0.name}"\nID #: "{0.id}"\nDiscriminator #: "{0.discriminator}"\nAvatar URL: "{0.avatar_url}"\nCurrent Status: "{2}"\nCurrent Game: "{3}"\nVoice channel they are in: "{4}"\nI have seen them in: "{1}" servers\nThey joined on: "{5}"\nRoles: "{6}"'.format(targetMember,seeinserver,str(targetMember.status),str(targetMember.game),str(targetMember.voice_channel),str(targetMember.joined_at),', '.join(map(str, targetMember.roles)).replace("@", "@\u200b"))
				await self.bot.say(xl.format(x))
			else:
				for user in users:
					server = ctx.message.server
					seeinserver = str(len(set([member.server.name for member in self.bot.get_all_members() if member.name == user.name])))
					x = 'Player Information:\nUsername: "{}"\nID #: "{}"\nDiscriminator #: "{}"\nAvatar URL: "{}"\nCurrent Status: "{}"\nCurrent Game: "{}"\nVoice channel they are in: "{}"\nI have seen them in: "{} servers"\nThey joined on: "{}"\nRoles: "{}"'.format(user.name,user.id,user.discriminator,user.avatar_url,str(user.status),str(user.game),str(user.voice_channel),seeinserver,str(user.joined_at),', '.join(map(str, user.roles)).replace("@", "@\u200b"))
					await self.bot.say(xl.format(x))
		except Exception as e:
			await self.bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

	@commands.command(pass_context=True)
	async def date(self,ctx):
		"""Gives the bots date and time."""
		try:
			await self.bot.say('{}:'.format(ctx.message.author.name) + '\nMy current date is: **' + time.strftime("%A, %B %d, %Y") + '**' + '\nMy current time is: **' + time.strftime("%I:%M:%S %p") + '**')
		except Exception as e:
			await self.bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

	@commands.command(pass_context=True)
	async def avatar(self,ctx,*users:discord.User):
		"""Gives the avatar of a user."""
		try:
			for user in users:
				await self.bot.say("{}'s current avatar is: \n".format(user.mention) + user.avatar_url)
		except Exception as e:
			await self.bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

	@commands.command(pass_context=True)
	async def weather(self,ctx,*,location:str):
		"""Gives the current weather in a city."""
		try:
			owm = pyowm.OWM('0a452fe77a83c5c2a6dd65d08f49bb18')
			observation = owm.weather_at_place(location)
			w = observation.get_weather()
			obs = w.get_detailed_status()
			if obs == 'clear sky':
				await self.bot.say("The weather is forcasted to be a clear sky :sunny:")
			elif obs == 'broken clouds':
				await self.bot.say("The weather is forcasted to be broken clouds :cloud:")
			else:
				await self.bot.say("The weather is forcasted to be " + obs.strip("'") + ".")
		except Exception as e:
			await self.bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

	@commands.command(pass_context=True)
	async def serverinfo(self,ctx):
		"""Gives information about the current server."""
		try:
			try:
				server = ctx.message.server
				if len(str(server.icon_url)) > 0:
					await self.bot.say('```xl\nServer Information:\nName: "' + server.name + '"\nID: "' + server.id + '"\nOwner: "' + str(server.owner) + '"\nRoles: "' + ', '.join(map(str, server.roles)).replace("@", "@\u200b") + '"\nReigon: "' + str(server.region) + '"\nChannels: "' + ', '.join(map(str, server.channels)) + '"\nDefault Channel: "' + str(server.default_channel) + '"\nMembers: "' + ', '.join(map(str, server.members)) + '"\nIcon: "' + str(server.icon_url) + '"\n```')
				else:
					await self.bot.say('```xl\nServer Information:\nName: "' + server.name + '"\nID: "' + server.id + '"\nOwner: "' + str(server.owner) + '"\nRoles: "' + ', '.join(map(str, server.roles)).replace("@", "@\u200b") + '"\nReigon: "' + str(server.region) + '"\nChannels: "' + ', '.join(map(str, server.channels)) + '"\nDefault Channel: "' + str(server.default_channel) + '"\nMembers: "' + ', '.join(map(str, server.members)) + '"\nIcon: "None"\n```')
			except HTTPException:
				if len(str(server.icon_url)) > 0:
					await self.bot.say('```xl\nServer Information:\nName: "' + server.name + '"\nID: "' + server.id + '"\nOwner: "' + str(server.owner) + '"\nRoles: "' + ', '.join(map(str, server.roles)).replace("@", "@\u200b") + '"\nReigon: "' + str(server.region) + '"\nChannels: "' + ', '.join(map(str, server.channels)) + '"\nDefault Channel: "' + str(server.default_channel) + '"\nMembers: "Too Many to Count >.<"\nIcon: "' + str(server.icon_url) + '"\n```')
				else:
					await self.bot.say('```xl\nServer Information:\nName: "' + server.name + '"\nID: "' + server.id + '"\nOwner: "' + str(server.owner) + '"\nRoles: "' + ', '.join(map(str, server.roles)).replace("@", "@\u200b") + '"\nReigon: "' + str(server.region) + '"\nChannels: "' + ', '.join(map(str, server.channels)) + '"\nDefault Channel: "' + str(server.default_channel) + '"\nMembers: "Too Many to Count >.<"\nIcon: "None"\n```')
		except Exception as e:
			await self.bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

	@commands.command(pass_context=True)
	async def join(self,ctx):
		"""Gives you my join information."""
		try:
			await self.bot.say("You can invite me to your server using: https://discordapp.com/oauth2/authorize?client_id=169558161047552002&scope=bot&permissions=261183" + "\n{0} needs all of these permissions to use commands like {1}prune or {1}ban! So if you don't want to use those types of features, feel free to uncheck them. But, if you do want to use them in the future, you will have to re-enable them.\n**Note: You have to be able to manage the server (edit the server settings) to invite me to your server, or else your desired server won't show up on the list!**".format(self.bot.user.name, config["command_prefix"]))
		except Exception as e:
			await self.bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

	@commands.command(pass_context=True)
	async def api(self,ctx,api=''):
			"""Gives information on various APIs."""
			if api == "steam":
				url = "https://steamgaug.es/api/v2"
				with aiohttp.ClientSession() as session:
					async with session.get(url) as resp:
						resp = await resp.json()
				if resp["ISteamClient"]["online"] == 1:
					SteamClient = "Online"
				else:
					SteamClient = "Offline"
				if resp["SteamCommunity"]["online"] == 1:
					SteamCommunity = "Online"
				else:
					SteamCommunity = "Offline"
				if resp["SteamStore"]["online"] == 1:
					SteamStore = "Online"
				else:
					SteamStore = "Offline"
				if resp["ISteamUser"]["online"] == 1:
					SteamUser = "Online"
				else:
					SteamUser = "Offline"
				if resp["IEconItems"]["440"]["online"] == 1:
					SteamTF2Items = "Online"
				else:
					SteamTF2Items = "Offline"
				if resp["IEconItems"]["570"]["online"] == 1:
					SteamDOTA2Items = "Online"
				else:
					SteamDOTA2Items = "Offline"
				if resp["IEconItems"]["730"]["online"] == 1:
					SteamCSGOItems = "Online"
				else:
					SteamCSGOItems = "Offline"
				if resp["ISteamGameCoordinator"]["440"]["online"] == 1:
					SteamTF2Games = "Online"
				else:
					SteamTF2Games = "Offline"
				if resp["ISteamGameCoordinator"]["570"]["online"] == 1:
					SteamDOTA2Games = "Online"
				else:
					SteamDOTA2Games = "Offline"
				if resp["ISteamGameCoordinator"]["730"]["online"] == 1:
					SteamCSGOGames = "Online"
				else:
					SteamCSGOGames = "Offline"
				x = 'Steam Statuses:\n	Steam Client: "{0}"\n	Steam Community: "{1}"\n	Steam Store: "{2}"\n	Steam Users: "{3}"\n	Item Servers:\n        TF2: "{4}"\n        DOTA 2: "{5}"\n        CS:GO: "{6}"\n	Game Coordinator:\n        TF2: "{7}"\n        DOTA 2: "{8}"\n        CS:GO: "{9}"'.format(SteamClient,SteamCommunity,SteamStore,SteamUser,SteamTF2Items,SteamDOTA2Items,SteamCSGOItems,SteamTF2Games,SteamDOTA2Games,SteamCSGOGames)
				await self.bot.say(xl.format(x))
			if api == "discord":
				url = "https://srhpyqt94yxb.statuspage.io/api/v2/summary.json"
				with aiohttp.ClientSession() as session:
					async with session.get(url) as resp:
						resp = await resp.json()
				x = 'Discord Statuses:\n	Overall Status: "{13}"\n    API: "{0}"\n	Gateway: "{1}"\n    CloudFlare: "{2}"\n    Voice: "{3}"\n        Amsterdam: "{4}"\n        Frankfurt: "{5}"\n        London: "{6}"\n        Singapore: "{7}"\n        Sydney: "{8}"\n        US Central: "{9}"\n        US East: "{10}"\n        US South: "{11}"\n        US West: "{12}"'.format(resp["components"][1]["status"],resp["components"][2]["status"],resp["components"][4]["status"],resp["components"][7]["status"],resp["components"][0]["status"],resp["components"][3]["status"],resp["components"][5]["status"],resp["components"][6]["status"],resp["components"][8]["status"],resp["components"][9]["status"],resp["components"][10]["status"],resp["components"][11]["status"],resp["components"][12]["status"],resp["status"]["description"])
				await self.bot.say(xl.format(x))

def setup(bot):
	bot.add_cog(Information(bot))