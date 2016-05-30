import time
import asyncio
from discord.ext import commands
import discord.utils
import pyowm
import json
from discord.errors import *
import requests
import aiohttp
from PIL import Image, ImageDraw, ImageFont

with open("mods/utils/json/configs/config.json") as f:
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
			owm = pyowm.OWM(config["OWMKey"])
			observation = owm.weather_at_place(location)
			w = observation.get_weather()
			obs = w.get_detailed_status()
			if obs == 'clear sky':
				await self.bot.say("The weather is forcasted to be a clear sky :sunny:")
			elif obs == 'broken clouds':
				await self.bot.say("The weather is forcasted to be broken clouds :cloud:")
			else:
				await self.bot.say("The weather is forcasted to be " + "".join(map(str,obs)) + ".")
		except Exception as e:
			await self.bot.say(wrap.format(type(e).__name__ + ': ' + str(e)))

	@commands.command(pass_context=True)
	async def weather1(self,ctx,*,location):
		with aiohttp.ClientSession() as session:
			url = "http://openweathermap.org/data/2.1/find/name?q={}".format(location)
			print(url)
			async with session.get(url) as resp:
				resp = await resp.json()
		print(resp)
		with aiohttp.ClientSession() as session:
			url = "http://openweathermap.org/img/w/{}.png".format(resp["list"][0]["weather"][0]["icon"])
			async with session.get(url) as resp:
				data = await resp.read()
				path = "mods/utils/images/weather/{}.png".format(resp["list"][0]["weather"][0]["icon"])
				with open(path,"wb") as f:
					f.write(data)
		wimg = Image.open("mods/utils/images/weather/{}.png".format(resp["list"][0]["weather"][0]["icon"]))
		img = Image.new('RGB', (1000, 500))
		d = ImageDraw.Draw(img)
		d.text(())

	@commands.command(pass_context=True)
	async def serverinfo(self,ctx):
		"""Gives information about the current server."""
		server = ctx.message.server
		if len(server.icon_url) < 1:
			url = "None"
		else:
			url = server.icon_url
		await self.bot.say(xl.format('Server Information:\nName: "{0.name}"\nID: "{0.id}"\nOwner: "{0.owner}"\nRegion: "{0.region}"\nDefault Channel: "{0.default_channel}"\nChannels: "{1}"\nMembers: "{2}"\nRoles: "{3}"\nIcon: "{4}"').format(server,len(server.channels),len(server.members),', '.join(map(str, server.roles)).replace("@", "@\u200b"),url))

	@commands.command(pass_context=True)
	async def join(self,ctx):
		"""Gives you my join information."""
		await self.bot.say("You can invite me to your server using: https://discordapp.com/oauth2/authorize?client_id=169558161047552002&scope=bot&permissions=261183" + "\n{0} needs all of these permissions to use commands like {1}prune or {1}ban! So if you don't want to use those types of features, feel free to uncheck them. But, if you do want to use them in the future, you will have to re-enable them.\n**Note: You have to be able to manage the server (edit the server settings) to invite me to your server, or else your desired server won't show up on the list!**".format(self.bot.user.name, config["command_prefix"]))

def setup(bot):
	bot.add_cog(Information(bot))