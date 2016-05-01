from random import randint,sample
import asyncio
from discord.ext import commands
import io
import discord.utils
import json
from discord.errors import *
import time
import aiohttp
import json

with open("mods/utils/config.json") as f:
	config = json.load(f)

wrap = "```py\n{}\n```"

class Fun():
	def __init__(self,bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def scramble(self,ctx,*,num:int):
		"""Allows the user to play a word scramble with the bot."""
		if num == 5:
			with open("mods/utils/5 letter words.txt", "r") as f:
				data = f.read()
			data = data.split("\n")
			i = randint(1, 5757)
			word = data[i-1]
			print(word)
			scrambled = sample(word, len(word))
			scrambled = ''.join(scrambled)
			await self.bot.say("The word scramble is: {}!".format(scrambled))
			await self.bot.wait_for_message(content=word)
			await self.bot.say("Nice job! You solved the scramble!")

	@commands.command(name="8ball",pass_context=True)
	async def cmd_8ball(self,ctx,*,msg:str):
		"""Allows the user to be bestowed the wisdom of the almighy Magic 8-Ball."""
		await self.bot.say('{} asked '.format(ctx.message.author.mention) + '`' + msg.replace("```","'''") + '`' + ': ' + config["eight_ball_replies"][randint(0, 19)])

	@commands.command(pass_context=True)
	async def rr(self,ctx):
		"""Allows the user to take part in the famous Russian Pasttime."""
		rr_bullet = randint(1, 6)
		rr_count = 1
		await self.bot.say('You spin the cylinder of the revolver with 1 bullet in it...')
		await asyncio.sleep(1)
		await self.bot.say('...you place the muzzle against your head and pull the trigger...')
		await asyncio.sleep(2)
		if rr_bullet == rr_count:
			await self.bot.say('...your brain gets splattered all over the wall.')
			rr_bullet = randint(1, 6)
			rr_count = 1
		else:
			await self.bot.say('...you live to see another day.')
			rr_count = rr_count + 1

	@commands.command(pass_context=True)
	async def shoot(self,ctx,*users:discord.User):
		"""Allows the user to shoot a person of choice."""
		for user in users:
			if user.id == self.bot.user.id:
				await self.bot.say('You attempted to shoot me, {}, but I dodged it!\nhttp://45.media.tumblr.com/c1165e983042a9cd1f17028a1c78170b/tumblr_n9c38m14291s5f9ado1_500.gif'.format(ctx.message.author.mention))
			elif user.id == ctx.message.author.id:
				await self.bot.say('{} commited suicide!\nhttps://media.giphy.com/media/5xaOcLAo1Gg0oRgBz0Y/giphy.gif'.format(ctx.message.author.mention))
			else:
				if user:
					await self.bot.say('{1} was shot dead by the mighty {0}!\nhttps://s-media-cache-ak0.pinimg.com/originals/2d/fa/a9/2dfaa995a09d81a07cad24d3ce18e011.gif'.format(ctx.message.author.mention, user.mention))
				else:
					await self.bot.say('You gotta give me someone to work with here!')

	@commands.command(pass_context=True)
	async def roti(self,ctx,*,number=''):
		"""Bestows the user with the 102 Rules of the Internet."""
		if not number:                
			with open("mods/utils/RulesOTI.txt", "r") as f:
				data = f.read()
			data = data.split("\n")
			i = randint(1, 102)
			await self.bot.say(data[i-1])
		else:
			try:
				i = int(number)
				if i > 0 and i <= 102:
					with open("mods/utils/RulesOTI.txt", "r") as f:
						data = f.read()
					data = data.split("\n")
					await self.bot.say(data[i-1])
				elif i >= 102 or i <= 0:
					await self.bot.say("It has to be a number between 1 and 102!")
			except ValueError:
				await self.bot.say("You have to put a number!")

	@commands.command(pass_context=True)
	async def lmgtfy(self,ctx,*,query):
		"""Gives the user a 'Let Me Google That For You' link."""
		msg = query.replace(' ','+')
		msg = 'http://lmgtfy.com/?q=%s' % msg
		await self.bot.say(msg)

	@commands.command(pass_context=True)
	async def pybelike(self,ctx):
		"""Gives the user an accurate description of Python."""
		await self.bot.send_file(ctx.message.channel, "mods/utils/python.png")

	@commands.command(pass_context=True)
	async def lenny(self,ctx):
		"""Gives the user a lenny face."""
		i = randint(1, 98)
		with io.open('mods/utils/lenny.txt','r',encoding='utf8') as f:
			text = f.read()
		text = text.split("\n")
		await self.bot.say("`" + text[i-1] + "`")

	@commands.command(pass_context=True)
	async def meh(self,ctx):
		"""Gives the user the famous shrug face."""
		i = 7
		with io.open('mods/utils/lenny.txt','r',encoding='utf8') as f:
			text = f.read()
		text = text.split("\n")
		await self.bot.say("" + text[i-1] + "")

	@commands.command(pass_context=True)
	async def emoji(self,ctx,query=""):
		"""Gives the user emojis.

			Do `^emoji url` to get the link to the cheat sheet page, or put a number from 1 to 874 to get a random emoji!"""
		if not query:
			with open("mods/utils/emoji.txt", "r") as f:
				data = f.read()
			data = data.split("\n")
			emoji1 = randint(1, 874)
			emoji2 = randint(1, 874)
			emoji3 = randint(1, 874)
			emoji4 = randint(1, 874)
			await self.bot.say("Some useful emojis are `" + data[emoji1-1] + "` " + data[emoji1-1] + ", `" + data[emoji2-1] + "` " + data[emoji2-1] + ", `" + data[emoji3-1] + "` " + data[emoji3-1] + ", and `" + data[emoji4-1] + "` " + data[emoji4-1] + "!")
		else:
			if query == "url":
				await self.bot.say("http://www.emoji-cheat-sheet.com/")
			else:
				with io.open('mods/utils/emoji.txt','r') as f:
					text = f.read()
				text = text.split("\n")
				i = int(query)
				await self.bot.say(text[i-1])

	@commands.command(pass_context=True)
	async def copypasta(self,ctx,query=''):
		"""Gives the user a random copypasta.

		Do `^copypasta <number from 1-19>` for a specific copypasta!
		"""
		if not query:
			with io.open('mods/utils/copypasta.txt','r',encoding='utf8') as f:
				data = f.read()
			data = data.split("\n")
			i = randint(1,19)
			await self.bot.say(data[i-1])
		else:
			with io.open('mods/utils/copypasta.txt','r',encoding='utf8') as f:
				data = f.read()
			data = data.split("\n")
			i = int(query)
			await self.bot.say(data[i-1])

	@commands.command(pass_context=True)
	async def nope(self,ctx):
		"""Gives a user a 'nope' gif."""
		with open("mods/utils/nope.txt","r") as f:
			data = f.read()
		data = data.split("\n")
		i = randint(1,3)
		await self.bot.say(data[i-1])

	@commands.command(pass_context=True)
	async def xkcd(self,ctx,query=""):
		"""Queries a random XKCD comic.

		Do `^xkcd <number from 1-1662>` to pick a specific comic."""
		if not query:
			i = randint(1, 1662)
			await self.bot.say("https://xkcd.com/{}/".format(i))
		elif query.isdigit() and int(query) >= 1 and int(query) <= 1662:
			await self.bot.say("https://xkcd.com/{}/".format(query))
		elif int(query) <= 0 or int(query) >= 1663:
			await self.bot.say("It has to be between 1 and 1662!")
		elif not query.isdigit():
			await self.bot.say("You have to put a number!")
		else:
			await self.bot.say("I don't know how you managed to do it, but you borked it.")

	@commands.command(pass_context=True)
	async def say(self,ctx,*,message):
		"""Makes the bot say anything the user wants it to."""
		await self.bot.say(message)

	@commands.command(pass_context=True)
	async def hexcolors(self,ctx):
		"""Gives a giant list of all hex colors and their values."""
		await self.bot.say("A *whole* list of hexidecimal color codes can be found here: http://xkcd.com/color/rgb.txt")

	@commands.command(pass_context=True)
	async def codeblock(self,ctx,language:str,*,code:str):
		"""Transforms the specified code into a code block with the coding language of choice."""
		if "```" in code:
			await self.bot.say("```{0}\n{1}\n```".format(language,code.replace("```","'''")))
		else:
			await self.bot.say("```{0}\n{1}\n```".format(language,code))

	@commands.command(pass_context=True)
	async def timer(self,ctx,seconds,*,remember=''):
		"""Sets a timer for a user with the option of setting a reminder text."""
		if not remember:
			endtimer = self.bot.say(ctx.message.author.mention + ', your timer for ' + seconds + ' seconds has expired!')
			await self.bot.say(ctx.message.author.mention + ', you have set a timer for ' + seconds + ' seconds!')
			await asyncio.sleep(float(seconds))
			await endtimer
		else:
			endtimer = self.bot.say(ctx.message.author.mention + ", your timer for " + seconds + " seconds has expired! I was instructed to remind you about `" + remember + "`!")
			await self.bot.say(ctx.message.author.mention + ", I will remind you about `" + remember + "` in " + seconds + " seconds!")
			await asyncio.sleep(float(seconds))
			await endtimer

	@commands.group(pass_context=True,invoke_without_command=True)
	async def meme(self,ctx,meme:str,line1:str,line2:str):
		"""Generates a meme."""
		if ctx.invoked_subcommand is None:
			await self.bot.say("http://memegen.link/{0}/{1}/{2}.jpg".format(meme,line1.replace("-","--").replace("_","__").replace(" ","-").replace(" ","_").replace("?","~q").replace("%","~p").replace("\"","''"),line2.replace("-","--").replace("_","__").replace(" ","-").replace(" ","_").replace("?","~q").replace("%","~p").replace("\"","''")))

	@meme.command(name="custom",pass_context=True)
	async def _custom(self,ctx,pic:str,line1:str,line2:str):
		"""Generates a meme using a custom picture."""
		if not ".gif" in pic[-5:]:
			await self.bot.say("http://memegen.link/custom/{0}/{1}.jpg?alt={2}".format(line1.replace("-","--").replace("_","__").replace(" ","-").replace(" ","_").replace("?","~q").replace("%","~p").replace("\"","''"),line2.replace("-","--").replace("_","__").replace(" ","-").replace(" ","_").replace("?","~q").replace("%","~p").replace("\"","''"),pic))
		else:
			await self.bot.say("You can't use gifs for memes!")

	@meme.group(name="templates",pass_context=True,invoke_without_command=True)
	async def _templates(self,ctx):
		"""Gives users a list of meme templates."""
		await self.bot.say("All stock templates can be found here: <{}>".format("http://memegen.link/templates/"))

	@_templates.command(name="search",pass_context=True)
	async def __search(self,ctx,searchtype,*,query):
		"""Searches the current usable meme templates.

			You also can look at examples of meme templates by passing 'example' in the searchtype field and put the abbreviated meme code in query."""
		if searchtype == "name":
			url = "http://memegen.link/templates/"
			query = query.title()
			query = query.replace("'A","'a").replace("'R","'r").replace("'S","'s").replace("'M","'m")
			print(query)
			with aiohttp.ClientSession() as session:
				async with session.get(url) as resp:
					resp = await resp.json()
			with open("mods/utils/memenames.json","w") as f:
				f.seek(0)
				f.write(json.dumps(resp))
				f.truncate()
			with open("mods/utils/memenames.json") as f:
				names = json.load(f)
			if query in names:
				q = names[query]
				await self.bot.say(q[30:])
			else:
				await self.bot.say("That isn't a real meme!")
		if searchtype == "example":
			await self.bot.say("http://memegen.link/{0}/your-text/goes-here.jpg".format(query))
				

def setup(bot):
	bot.add_cog(Fun(bot))