import asyncio
from discord.ext import commands
from discord.errors import *
import json
import discord
import aiohttp
from bs4 import BeautifulSoup as bs
from googleapiclient.discovery import build
from random import randint

with open("mods/utils/json/configs/config.json") as f:
	config = json.load(f)
with open("mods/utils/json/configs/credentials.json") as f:
	credentials = json.load(f)

wrap = "```py\n{0}\n```"
xl = "```xl\n{0}\n```"

class Internet():
	def __init__(self,bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def penguin(self,ctx):
		"""Penguins!"""
		url = "http://penguin.wtf/"
		with aiohttp.ClientSession() as session:
			async with session.get(url) as resp:
				r = await resp.read()
		resp = bs(r,'html.parser')
		await self.bot.say(resp.text)

	@commands.command(pass_context=True)
	async def search(self,ctx,*,query:str):
		"""Searches Google for your queries."""
		service = build('customsearch','v1',developerKey=credentials['developerKey'])
		resp = service.cse().list(q=query,cx=credentials['cx']).execute()
		await self.bot.say(":mag:**{}**:\n\n{}\n\n{}".format(resp['items'][0]['title'],resp['items'][0]['snippet'].lstrip("\n"),resp['items'][0]['link']))

	@commands.command(pass_context=True)
	async def insult(self,ctx,user:discord.User=None):
		"""Insults a user."""
		url = "http://www.insultgenerator.org/"
		with aiohttp.ClientSession() as session:
			async with session.get(url) as resp:
				r = await resp.read()
		resp = bs(r,'html.parser')
		if user is not None:
			pre = user.name + ": "
		else:
			pre = ""
		await self.bot.say(pre + resp.find('div', {'class':'wrap'}).text.strip("\n"))

	@commands.command(pass_context=True)
	async def urband(self,ctx,*,query:str):
		"""Finds a phrase in the Urban Dictionary."""
		url = "http://www.urbandictionary.com/define.php?term={}".format(query.replace(" ","%20"))
		with aiohttp.ClientSession() as session:
			async with session.get(url) as resp:
				r = await resp.read()
		resp = bs(r,'html.parser')
		try:
			if len(resp.find('div', {'class':'meaning'}).text.strip('\n').replace("\u0027","'")) >= 1000:
				meaning = resp.find('div', {'class':'meaning'}).text.strip('\n').replace("\u0027","'")[:1000] + "..."
			else:
				meaning = resp.find('div', {'class':'meaning'}).text.strip('\n').replace("\u0027","'")
			await self.bot.say(":mag:**{0}**: \n{1}\n\n**Example**: \n{2}\n\n**~{3}**".format(query,meaning,resp.find('div', {'class':'example'}).text.strip('\n'),resp.find('div', {'class':'contributor'}).text.strip('\n')))
		except AttributeError:
			await self.bot.say("Either the page doesn't exist, or you typed it in wrong. Either way, please try again.")

	@commands.command(pass_context=True)
	async def rip(self,ctx,user:discord.User):
		"""RIP."""
		if not user.nick == None:
			user = user.nick
		else:
			user = user.name
		await self.bot.say("<http://ripme.xyz/{}>".format(user.replace(" ","%20")))

	@commands.command(pass_context=True)
	async def robohash(self,ctx,user:discord.User):
		"""Robot pics."""
		if not user.nick == None:
			user = user.nick
		else:
			user = user.name
		await self.bot.say("https://robohash.org/{}.png".format(user.replace(" ","%20")))

	@commands.command(pass_context=True)
	async def xkcd(self,ctx,query=""):
		"""Queries a random XKCD comic.

		Do `^xkcd <number from 1-1662>` to pick a specific comic."""
		if not query:
			i = randint(1, 1662)
			url = "https://xkcd.com/{}/".format(i)
		elif query.isdigit() and int(query) >= 1 and int(query) <= 1662:
			url = "https://xkcd.com/{}/".format(query)
		elif int(query) <= 0 or int(query) >= 1663:
			await self.bot.say("It has to be between 1 and 1662!")
		elif not query.isdigit():
			await self.bot.say("You have to put a number!")
		else:
			await self.bot.say("I don't know how you managed to do it, but you borked it.")
		with aiohttp.ClientSession() as session:
			async with session.get(url) as resp:
				r = await resp.read()
		resp = bs(r,'html.parser')
		await self.bot.say(":mag:**" + resp('img')[1]['alt'] + "**\nhttp:" + resp('img')[1]['src'] + "\n" + resp('img')[1]['title'])

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
	bot.add_cog(Internet(bot))