from discord.ext import commands
from .utils import checks
import asyncio
import discord.utils
from discord.errors import *

wrap = "```py\n{}\n```"

class ServerModeration():
	def __init__(self,bot):
		self.bot = bot

	@commands.command(pass_context=True)
	@checks.mod_or_perm(manage_server=True)
	async def listbans(self,ctx):
		"""Lists the current bans on the server."""
		server = ctx.message.server
		bans = await self.bot.get_bans(server)
		if len(bans) == 0:
			await self.bot.say("There are no active bans currently on the server.")
		else:
			await self.bot.say("The currently active bans for this server are: " + ", ".join(map(str, bans)))

	@commands.command(pass_context=True)
	@checks.admin_or_perm(manage_server=True)
	async def kick(self,ctx,*users:discord.User):
		"""Kicks the user of choice."""
		server = ctx.message.server
		for member in ctx.message.mentions:
			member = discord.utils.find(lambda m: m.name == member.name, ctx.message.channel.server.members)
			try:
				await self.bot.kick(member)
				await self.bot.say(member.name + " was kicked from the server.")
				break
			except HTTPException:
				await self.bot.say("Kicking failed. Sorry..")
				return
		else:
			await self.bot.say('A username may help..')

	@commands.command(pass_context=True)
	@checks.admin_or_perm(manage_server=True)
	async def prunekick(self,ctx,*users:discord.User):
		"""Kicks a user and deletes 7 days of their messages."""
		server = ctx.message.server
		for member in ctx.message.mentions:
			member = discord.utils.find(lambda m: m.name == member.name, ctx.message.channel.server.members)
			try:
				await self.bot.ban(member, delete_message_days=7)
				await self.bot.unban(member.server, member)
				await self.bot.say(member.name + " was prune kicked from the server.")
				break
			except HTTPException:
				await self.bot.say("Prune kick failed. Sorry...")
				return
		else:
			await self.bot.say('A username may help..')

	@commands.command(pass_context=True)
	@checks.admin_or_perm(manage_server=True)
	async def ban(self,ctx,*users:discord.User):
		"""Bans a user and deletes their messages."""
		server = ctx.message.server
		for member in ctx.message.mentions:
			member = discord.utils.find(lambda m: m.name == member.name, ctx.message.channel.server.members)
			try:
				await self.bot.ban(member, delete_message_days=7)
				await self.bot.say(member.name + " was banned from the server.")
				break
			except HTTPException:
				await self.bot.say("Banning failed. Sorry...")
				return
		else:
			await self.bot.say('A username may help..')

	@commands.command(pass_context=True)
	@checks.admin_or_perm(manage_messages=True)
	async def prune(self,ctx,messages):
		"""Deletes x amount of messages in a channel."""
		message = ctx.message
		if messages.isdigit():
			n = int(messages)
			removed = 0
			async for x in self.bot.logs_from(message.channel, limit=n+1):
				await self.bot.delete_message(x)
				removed += 1
				await asyncio.sleep(.21)
			x = await self.bot.say("Removed {} messages".format(removed))
			await asyncio.sleep(5)
			await self.bot.delete_message(x)
		else:
			await self.bot.say("You have to put in a digit!")

	@commands.command(pass_context=True)
	@checks.mod_or_perm()
	async def createinv(self,ctx):
		"""Creates an instant invite."""
		server = ctx.message.server
		invite = await self.bot.create_invite(server)
		await self.bot.say(invite)

	@commands.command(pass_context=True)
	@checks.mod_or_perm()
	async def deleteinv(self,ctx,invite:str):
		"""Deletes/Deactivates an invite."""
		server = ctx.message.server
		await self.bot.delete_invite(invite)
		await self.bot.say("Successfully deleted the invite!")

	@commands.command(pass_context=True)
	@checks.mod_or_perm(manage_server=True)
	async def listinvs(self,ctx):
		"""Lists the currently active invites on the server."""
		server = ctx.message.server
		invs = await self.bot.invites_from(server)
		if len(invs) == 0:
			await self.bot.say("There are no active invites currently on the server.")
		else:
			await self.bot.say("The currently active invites for this server are: " + ", ".join(map(str, invs)))

	@commands.command(pass_context=True)
	@checks.mod_or_perm(manage_messages=True)
	async def clean(self,ctx, max_messages:int):
		"""Removes any messages from the bot in x amount of messages."""
		if max_messages > 1000:
			await self.bot.say("I can't go searching through more than 1000 messages!")
		removed = 0
		async for message in self.bot.logs_from(ctx.message.channel, limit=max_messages):
			if message.author == self.bot.user:
				asyncio.ensure_future(self.bot.delete_message(message))
				removed += 1
				await asyncio.sleep(.21)
		x = await self.bot.say("Removed {} messages".format(removed))
		await asyncio.sleep(5)
		await self.bot.delete_message(x)

	@commands.command(pass_context=True)
	@checks.admin_or_perm(manage_server=True)
	async def createrole(self,ctx,*,role):
		"""Creates a server role."""
		server = ctx.message.server
		await self.bot.create_role(server, name=role)
		await self.bot.say("Alright, I created the role `{}`".format(role))

	@commands.command(pass_context=True)
	@checks.admin_or_perm(manage_server=True)
	async def addrole(self,ctx,role:discord.Role,*users:discord.User):
		"""Adds a role to x users."""
		if len(users) == 0:
			await self.bot.say("You need to add a person to give the role to!")
		for user in users:
			await self.bot.add_roles(user, role)
		await self.bot.say("Giving " + ", ".join(map(str,users)) + " the role {}".format(role))

	@commands.command(pass_context=True)
	@checks.admin_or_perm(manage_server=True)
	async def removerole(self,ctx,role:discord.Role,*users:discord.User):
		"""Removes a role from x users."""
		if len(users) == 0:
			await self.bot.say("You need to add a person to remove the role from!")
		await self.bot.say("Removing  the role {} from ".format(role) + ", ".join(map(str,users)))
		for user in users:
			await self.bot.remove_roles(user, role)

	@commands.command(pass_context=True)
	@checks.admin_or_perm(manage_server=True)
	async def deleterole(self,ctx,*,role:discord.Role):
		"""Deletes a role from the server."""
		server = ctx.message.server
		await self.bot.delete_role(server,role)
		await self.bot.say("Alright, I deleted the role `{}` from the server!".format(role))

	@commands.command(pass_context=True)
	@checks.admin_or_perm(manage_server=True)
	async def color(self,ctx,role:discord.Role,color:discord.Color):
		"""Changes the color of a role.

			For example, to change the color of Dank Rank to white, I would do ^color 'Dank Rank' 0xFFFFFF"""
		server = ctx.message.server
		await self.bot.edit_role(server,role,color=discord.Color(color))
		await self.bot.say("Alright, I changed the role `{}`'s to the hex color `{}`!".format(role,color))

	@commands.command(pass_context=True)
	@checks.admin_or_perm(manage_server=True)
	async def leave(self,ctx):
		"""Makes me leave the server."""
		server = ctx.message.server
		await self.bot.say("Alright, everyone! I'm off to a new life elsewhere! Until next time! :wave:")
		await self.bot.leave_server(server)

	@commands.command(pass_context=True)
	@checks.admin_or_perm(manage_server=True)
	async def changenick(self,ctx,nickname,*users:discord.User):
		"""Changes users nicknames."""
		for user in users:
			await self.bot.change_nickname(user,nickname)
			await self.bot.say("Alright, I changed the nickname of `{}` to `{}`".format(user,nickname))

def setup(bot):
	bot.add_cog(ServerModeration(bot))