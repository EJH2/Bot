"""
Moderation commands.
"""

import asyncio

import discord
from discord.ext import commands

from discordbot.cogs.utils import config
from discordbot.cogs.utils.checks import permissions


# noinspection PyTypeChecker
class Moderation:
    def __init__(self, bot):
        self.bot = bot
        self.ignored = config.Config("ignored.yaml")

    # =================================
    #   Blacklisting related commands
    # =================================

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @commands.check(permissions(manage_channels=True))
    async def ignore(self, ctx):
        """
        Command for ignoring the channel/server.
        """
        await ctx.send("Invalid subcommand passed: {0.subcommand_passed}".format(ctx), delete_after=5)

    @ignore.command(name="list")
    @commands.guild_only()
    async def ignore_list(self, ctx):
        """
        Grabs a list of currently ignored channels in the server.
        """
        ignored = self.ignored.get("channels", [])
        channel_ids = set(c.id for c in ctx.message.guild.channels)
        result = []
        for channel in ignored:
            if channel in channel_ids:
                result.append("<#{}>".format(channel))

        if result:
            await ctx.send("The following channels are ignored:\n\n{}".format(", ".join(result)), delete_after=5)
        else:
            await ctx.send("I am not ignoring any channels here.", delete_after=5)

    @ignore.command(name="channel")
    @commands.check(permissions(manage_channels=True))
    async def ignore_channel(self, ctx, *, channel: discord.TextChannel = None):
        """Ignores a specific channel from being read by the bot.

        If you don"t specify a channel the current channel will be ignored.
        To use this you need Manage Channels.
        """

        if channel is None:
            channel = ctx.message.channel

        ignored = self.ignored.get("channels", [])
        if channel.id in ignored:
            await ctx.send("That channel is already ignored.", delete_after=5)
            return

        ignored.append(channel.id)
        self.ignored.place("channels", ignored)
        await ctx.send("I am no longer reading from that channel.", delete_after=5)

    @ignore.command(name="server")
    @commands.check(permissions(manage_server=True))
    async def ignore_server(self, ctx):
        """Ignores the whole server from the bot.

        To use this you need Manage Server.
        """

        ignored = self.ignored.get("channels", [])
        channels = ctx.message.guild.channels
        ignored.extend(c.id for c in channels if c.type == discord.ChannelType.text)
        self.ignored.place("channels", list(set(ignored)))  # make unique
        await ctx.send("I am now ignoring this server.", delete_after=5)

    @commands.group()
    @commands.guild_only()
    @commands.check(permissions(manage_channels=True))
    async def unignore(self, ctx):
        """
        Command for un-ignoring channels/the server.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand passed: {0.subcommand_passed}".format(ctx), delete_after=5)

    @unignore.command(name="channel")
    @commands.guild_only()
    @commands.check(permissions(manage_channels=True))
    async def unignore_channel(self, ctx, channel: discord.TextChannel = None):
        """Unignores channels from being read by the bot.

        If no channels are specified, it unignores the current channel.
        To use this you need Manage Channels.
        """

        if not channel:
            channel = ctx.message.channel

        # a set is the proper data type for the ignore list
        # however, JSON only supports arrays and objects not sets.
        ignored = self.ignored.get("channels", [])
        if channel.id not in ignored:
            await ctx.send("I am not currently ignoring that channel.", delete_after=5)
            return

        self.ignored.remove("channels", channel.id)

        self.ignored.place("channels", ignored)
        await ctx.send("I am now reading from that channel.", delete_after=5)

    @unignore.command(name="server")
    @commands.guild_only()
    @commands.check(permissions(manage_server=True))
    async def unignore_server(self, ctx):
        """
        Un-ignores all channels in this server from being read by the bot.

        To use this you need Manage Server.
        """
        channels = [c for c in ctx.message.guild.channels if c.type is discord.channel.ChannelType.text]
        ignored = self.ignored.get("channels", [])
        for channel in channels:
            try:
                self.ignored.remove("channels", channel.id)
            except ValueError:
                pass

        self.ignored.place("channels", ignored)
        await ctx.send("I am now reading from this server.", delete_after=5)

    # ============================
    #   Banning related commands
    # ============================

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(manage_server=True))
    async def listbans(self, ctx):
        """
        Lists the current bans on the server.
        """
        bans = await ctx.message.guild.bans()
        if len(bans) == 0:
            await ctx.send("There are no active bans currently on the server.")
        else:
            await ctx.send("The currently active bans for this server are: " + ", ".join(map(str, bans)))

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(manage_server=True))
    async def kick(self, ctx, *members: discord.Member):
        """
        Kicks the member of choice.
        """
        for member in members:
            try:
                await ctx.message.guild.kick(member)
                await ctx.send(member.name + " was kicked from the server.")
            except discord.errors.Forbidden:
                await ctx.send("Skipping `{}`, permissions error.".format(member))

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(manage_server=True))
    async def softban(self, ctx, *members: discord.Member):
        """
        Kicks a member and deletes 7 days of their messages.
        """
        for member in members:
            try:
                await ctx.message.guild.ban(member, delete_message_days=7)
                await ctx.message.guild.unban(member.server, member)
                await ctx.send(member.name + " was softbanned from the server.")
                await asyncio.sleep(1)
            except discord.errors.Forbidden:
                await ctx.send("Skipping `{}`, permissions error.".format(member))

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(manage_server=True))
    async def ban(self, ctx, *members: discord.Member):
        """
        Bans a member and deletes their messages.
        """
        banned = 0
        for member in members:
            try:
                await ctx.message.guild.ban(member, delete_message_days=7)
                banned += 1
            except discord.errors.DiscordException as e:
                try:
                    await ctx.send("User `{}` (ID: `{}`) could not be banned: `{}`".format(str(member), member.id, e))
                except discord.errors.DiscordException as err:
                    await ctx.send("User `{}` could not be banned: `{}`".format(member, err))
        await ctx.send("Successfully banned {}/{} users".format(banned, len(members)))

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(manage_server=True))
    async def unban(self, ctx, *, name: str):
        """
        Unbans a member.
        """
        bans = await ctx.message.guild.bans()
        member = discord.utils.get(bans, user__name=name)
        if member:
            await ctx.message.guild.unban(member.user)
            await ctx.send("{0.name}#{0.discriminator} has been unbanned from the server!".format(member.user))
            return
        await ctx.send("You can't unban a member that hasn't been banned!")

    @commands.command()
    @commands.guild_only()
    async def hackban(self, ctx, *user_ids: int):
        """
        Preemptive bans a user.
        """
        banned = 0
        for user_id in user_ids:
            try:
                await ctx.message.guild.ban(discord.Object(id=user_id))
                banned += 1
            except discord.errors.DiscordException as e:
                try:
                    user = await ctx.bot.get_user_info(user_id)
                    await ctx.send("User `{}` (ID: `{}`) could not be banned: `{}`".format(str(user), user.id, e))
                except discord.errors.DiscordException as err:
                    await ctx.send("User `{}` could not be banned: `{}`".format(user_id, err))
        await ctx.send("Successfully banned {}/{} users".format(banned, len(user_ids)))

    @commands.command()
    @commands.check(permissions(manage_guild=True, kick_members=True, ban_members=True))
    async def leave(self, ctx):
        """
        Makes me leave the server.
        """
        server = ctx.message.guild
        await ctx.send("Alright, everyone! I'm off to a new life elsewhere! Until next time! :wave:")
        await server.leave()

    # =========================
    #   Chat related commands
    # =========================

    @commands.command()
    @commands.check(permissions(manage_messages=True))
    async def prune(self, ctx, messages: int = 100):
        """
        Deletes x amount of messages in a channel.
        """
        await ctx.message.channel.purge(limit=messages + 1)
        removed = messages + 1
        x = await ctx.send("Removed {} messages".format(removed))
        await asyncio.sleep(5)
        await x.delete()

    @commands.command()
    @commands.check(permissions(manage_messages=True))
    async def clean(self, ctx, messages: int = 100):
        """
        Deletes x amount of messages from the bot in a channel.
        """
        removed = 0
        async for message in ctx.message.channel.history():
            if message.author == ctx.bot.user and removed <= messages - 1:
                await message.delete()
                await asyncio.sleep(.21)
                removed += 1
        x = await ctx.send("Removed {} messages".format(removed))
        await asyncio.sleep(5)
        await x.delete()

    # ===========================
    #   Invite related commands
    # ===========================

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def invites(self, ctx):
        """
        Command for server invites.
        """
        await ctx.send("Invalid subcommand passed: {0.subcommand_passed}".format(ctx))

    @invites.command(name="create")
    async def invites_create(self, ctx):
        """
        Creates an instant invite.
        """
        invite = await ctx.message.guild.create_invite()
        await ctx.send(invite)

    @invites.command(name="delete")
    @commands.check(permissions(manage_server=True))
    async def invites_delete(self, ctx, invite: str):
        """
        Deletes/Deactivates an invite.
        """
        await ctx.message.guild.delete_invite(invite)
        await ctx.send("Successfully deleted the invite!")

    @invites.command(name="list")
    @commands.check(permissions(manage_server=True))
    async def invites_list(self, ctx):
        """
        Lists the currently active invites on the server.
        """
        invs = await ctx.message.guild.invites()
        if len(invs) == 0:
            await ctx.send("There are no active invites currently on the server.")
        else:
            await ctx.send("The currently active invites for this server are: " + ", ".join(map(str, invs)))

    # =========================
    #   Role related commands
    # =========================

    @commands.group()
    @commands.guild_only()
    @commands.check(permissions(manage_roles=True))
    async def roles(self, ctx):
        """
        Command for server roles.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand passed: {0.subcommand_passed}".format(ctx))

    @roles.command(name="create")
    @commands.check(permissions(manage_roles=True))
    async def roles_create(self, ctx, *, role):
        """
        Creates a server role.
        """
        await ctx.message.guild.create_role(name=role)
        await ctx.send("Alright, I created the role `{}`".format(role))

    @roles.command(name="add")
    @commands.check(permissions(manage_roles=True))
    async def roles_add(self, ctx, role: discord.Role, *members: discord.Member):
        """
        Adds a role to x members.
        """
        if len(members) == 0:
            await ctx.send("You need to add a person to give the role to!")
        for member in members:
            try:
                await member.add_roles(role)
                await asyncio.sleep(1)
            except discord.errors.Forbidden:
                await ctx.send("Skipping `{}`, permissions error.".format(member))
        await ctx.send("Giving " + ", ".join(map(str, members)) + " the role {}".format(role))

    @roles.command(name="remove")
    @commands.check(permissions(manage_roles=True))
    async def roles_remove(self, ctx, role: discord.Role, *members: discord.Member):
        """
        Removes a role from x members.
        """
        if len(members) == 0:
            await ctx.send("You need to add a person to remove the role from!")
        await ctx.send("Removing  the role {} from ".format(role) + ", ".join(map(str, members)))
        for member in members:
            try:
                await member.remove_roles(role)
                await asyncio.sleep(.21)
            except discord.errors.Forbidden:
                await ctx.send("Skipping `{}`, permissions error.".format(member))
        await ctx.send("Roles removed!")

    @roles.command(name="delete")
    @commands.check(permissions(manage_roles=True))
    async def roles_delete(self, ctx, *, role: discord.Role):
        """
        Deletes a role from the server.
        """
        await ctx.message.guild.delete_role(role)
        await ctx.send("Alright, I deleted the role `{}` from the server.".format(role))

    @roles.command(name="color")
    @commands.check(permissions(manage_roles=True))
    async def roles_color(self, ctx, role: discord.Role, hexcolor: discord.Color):
        """
        Changes the color of a role.
        """
        await ctx.message.guild.edit_role(role, color=hexcolor)
        await ctx.send("Alright, I changed the role `{}` to the hex color `{}`".format(role, hexcolor))

    @roles.command(name="move")
    @commands.check(permissions(manage_roles=True))
    async def roles_move(self, ctx, role: discord.Role, position: int):
        """
        Moves a role's position in a server list.
        """
        await ctx.message.guild.move_role(role, position)
        await ctx.send("Alright, I moved the role {} to position {}".format(role, position))

    # =============================
    #   Nickname related commands
    # =============================

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(manage_server=True))
    async def changenick(self, ctx, nickname, *members: discord.Member):
        """
        Changes members nicknames.
        """
        for member in members:
            try:
                await member.edit(nick=nickname)
                await ctx.send("Alright, I changed the nickname of `{}` to `{}`".format(member, nickname))
                await asyncio.sleep(.21)
            except discord.errors.Forbidden:
                await ctx.send("Skipping `{}`, permissions error.".format(member))

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(manage_server=True))
    async def massnick(self, ctx, *, nickname):
        """
        Mass renames everyone in the server.
        """
        for member in ctx.message.guild.members:
            try:
                await member.edit(nick=nickname)
                await ctx.send("Alright, I changed the nickname of `{}` to `{}`".format(member, nickname))
                await asyncio.sleep(.21)
            except discord.errors.Forbidden:
                await ctx.send("Skipping `{}`, permissions error.".format(member))

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(manage_server=True))
    async def massunnick(self, ctx):
        """
        Mass un-names everyone in the server.
        """
        for member in ctx.message.guild.members:
            if member.nick:
                try:
                    await member.edit(nick=None)
                    await ctx.send("Alright, I reset the nickname of `{}`".format(member))
                    await asyncio.sleep(.21)
                except discord.errors.Forbidden:
                    await ctx.send("Skipping `{}`, permissions error.".format(member))


def setup(bot):
    bot.add_cog(Moderation(bot))
