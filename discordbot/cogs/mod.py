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

    @commands.group(no_pm=True, invoke_without_command=True)
    @commands.check(permissions(manage_channels=True))
    async def ignore(self, ctx):
        """
        Command for ignoring the channel/server.
        """
        await ctx.send("Invalid subcommand passed: {0.subcommand_passed}".format(ctx), delete_after=5)

    @ignore.command(name="list", no_pm=True)
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
    async def ignore_channel(self, ctx, *, channel: discord.channel.ChannelType.text = None):
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

    @ignore.command(name="server", pass_context=True)
    @commands.check(permissions(manage_server=True))
    async def ignore_server(self, ctx):
        """Ignores the whole server from the bot.

        To use this you need Manage Server.
        """

        ignored = self.ignored.get("channels", [])
        channels = ctx.message.server.channels
        ignored.extend(c.id for c in channels if c.type == discord.ChannelType.text)
        self.ignored.place("channels", list(set(ignored)))  # make unique
        await self.bot.say("I am now ignoring this server.", delete_after=5)

    @commands.group(pass_context=True, no_pm=True)
    @commands.check(permissions(manage_channels=True))
    async def unignore(self, ctx):
        """
        Command for un-ignoring channels/the server.
        """
        if ctx.invoked_subcommand is None:
            await self.bot.say("Invalid subcommand passed: {0.subcommand_passed}".format(ctx), delete_after=5)

    @unignore.command(name="channel", pass_context=True, no_pm=True)
    @commands.check(permissions(manage_channels=True))
    async def unignore_channel(self, ctx, channel: discord.Channel = None):
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
            await self.bot.say("I am not currently ignoring that channel.", delete_after=5)
            return

        self.ignored.remove("channels", channel.id)

        self.ignored.place("channels", ignored)
        await self.bot.say("I am now reading from that channel.", delete_after=5)

    @unignore.command(name="server", pass_context=True, no_pm=True)
    @commands.check(permissions(manage_server=True))
    async def unignore_server(self, ctx):
        """
        Un-ignores all channels in this server from being read by the bot.

        To use this you need Manage Server.
        """
        channels = [c for c in ctx.message.server.channels if c.type is discord.ChannelType.text]
        ignored = self.ignored.get("channels", [])
        for channel in channels:
            try:
                self.ignored.remove("channels", channel.id)
            except ValueError:
                pass

        self.ignored.place("channels", ignored)
        await self.bot.say("I am now reading from this server.", delete_after=5)

    # ============================
    #   Banning related commands
    # ============================

    @commands.command(pass_context=True)
    @commands.check(permissions(manage_server=True))
    async def listbans(self, ctx):
        """
        Lists the current bans on the server.
        """
        server = ctx.message.server
        bans = await self.bot.get_bans(server)
        if len(bans) == 0:
            await self.bot.say("There are no active bans currently on the server.")
        else:
            await self.bot.say("The currently active bans for this server are: " + ", ".join(map(str, bans)))

    @commands.command()
    @commands.check(permissions(manage_server=True))
    async def kick(self, *members: discord.Member):
        """
        Kicks the member of choice.
        """
        for member in members:
            try:
                await self.bot.kick(member)
                await self.bot.say(member.name + " was kicked from the server.")
            except discord.errors.Forbidden:
                await self.bot.say("Skipping `{}`, permissions error.".format(member))

    @commands.command()
    @commands.check(permissions(manage_server=True))
    async def softban(self, *members: discord.Member):
        """
        Kicks a member and deletes 7 days of their messages.
        """
        for member in members:
            try:
                await self.bot.ban(member, delete_message_days=7)
                await self.bot.unban(member.server, member)
                await self.bot.say(member.name + " was softbanned from the server.")
            except discord.errors.Forbidden:
                await self.bot.say("Skipping `{}`, permissions error.".format(member))

    @commands.command()
    @commands.check(permissions(manage_server=True))
    async def ban(self, *members: discord.Member):
        """
        Bans a member and deletes their messages.
        """
        for member in members:
            try:
                await self.bot.ban(member, delete_message_days=7)
                await self.bot.say(member.name + " was banned from the server.")
            except discord.errors.Forbidden:
                await self.bot.say("Skipping `{}`, permissions error.".format(member))

    @commands.command(pass_context=True)
    @commands.check(permissions(manage_server=True))
    async def unban(self, ctx, *, name: str):
        """
        Unbans a member.
        """
        server = ctx.message.server
        bans = await self.bot.get_bans(server)
        member = discord.utils.get(bans, name=name)
        if member:
            await self.bot.unban(server, member)
            await self.bot.say("{0.name}#{0.discriminator} has been unbanned from the server!".format(member))
            return
        await self.bot.say("You can't unban a member that hasn't been banned!")

    @commands.command(pass_context=True)
    async def hackban(self, ctx, user_id: int):
        """
        Preemptive bans a user.
        """
        try:
            await self.bot.http.ban(user_id, ctx.message.server.id)
            await self.bot.say("That user was banned from the server.")
        except discord.errors.NotFound:
            await self.bot.say("User does not seem to exist. Please make sure you are not copying the wrong ID.")

    @commands.command(pass_context=True)
    @commands.check(permissions(manage_server=True))
    async def leave(self, ctx):
        """
        Makes me leave the server.
        """
        server = ctx.message.server
        await self.bot.say("Alright, everyone! I'm off to a new life elsewhere! Until next time! :wave:")
        await self.bot.leave_server(server)

    # =========================
    #   Chat related commands
    # =========================

    @commands.command(pass_context=True)
    @commands.check(permissions(manage_messages=True))
    async def prune(self, ctx, messages: int = 100):
        """
        Deletes x amount of messages in a channel.
        """
        await self.bot.purge_from(ctx.message.channel, limit=messages + 1)
        removed = messages + 1
        x = await self.bot.say("Removed {} messages".format(removed))
        await asyncio.sleep(5)
        await self.bot.delete_message(x)

    @commands.command(pass_context=True)
    @commands.check(permissions(manage_messages=True))
    async def clean(self, ctx, messages: int = 100):
        """
        Deletes x amount of messages from the bot in a channel.
        """
        removed = 0
        async for message in self.bot.logs_from(ctx.message.channel):
            if message.author == self.bot.user and removed <= messages - 1:
                await self.bot.delete_message(message)
                await asyncio.sleep(.21)
                removed += 1
        x = await self.bot.say("Removed {} messages".format(removed))
        await asyncio.sleep(5)
        await self.bot.delete_message(x)

    # ===========================
    #   Invite related commands
    # ===========================

    @commands.group(pass_context=True, no_pm=True, invoke_without_command=True)
    async def invites(self, ctx):
        """
        Command for server invites.
        """
        await self.bot.say("Invalid subcommand passed: {0.subcommand_passed}".format(ctx))

    @invites.command(name="create", pass_context=True)
    async def invites_create(self, ctx):
        """
        Creates an instant invite.
        """
        invite = await self.bot.create_invite(ctx.message.server)
        await self.bot.say(invite)

    @invites.command(name="delete")
    @commands.check(permissions(manage_server=True))
    async def invites_delete(self, invite: str):
        """
        Deletes/Deactivates an invite.
        """
        await self.bot.delete_invite(invite)
        await self.bot.say("Successfully deleted the invite!")

    @invites.command(name="list", pass_context=True)
    @commands.check(permissions(manage_server=True))
    async def invites_list(self, ctx):
        """
        Lists the currently active invites on the server.
        """
        invs = await self.bot.invites_from(ctx.message.server)
        if len(invs) == 0:
            await self.bot.say("There are no active invites currently on the server.")
        else:
            await self.bot.say("The currently active invites for this server are: " + ", ".join(map(str, invs)))

    # =========================
    #   Role related commands
    # =========================

    @commands.group(pass_context=True, no_pm=True)
    @commands.check(permissions(manage_roles=True))
    async def roles(self, ctx):
        """
        Command for server roles.
        """
        if ctx.invoked_subcommand is None:
            await self.bot.say("Invalid subcommand passed: {0.subcommand_passed}".format(ctx))

    @roles.command(name="create", pass_context=True)
    @commands.check(permissions(manage_roles=True))
    async def roles_create(self, ctx, *, role):
        """
        Creates a server role.
        """
        server = ctx.message.server
        await self.bot.create_role(server, name=role)
        await self.bot.say("Alright, I created the role `{}`".format(role))

    @roles.command(name="add")
    @commands.check(permissions(manage_roles=True))
    async def roles_add(self, role: discord.Role, *members: discord.Member):
        """
        Adds a role to x members.
        """
        if len(members) == 0:
            await self.bot.say("You need to add a person to give the role to!")
        for member in members:
            try:
                await self.bot.add_roles(member, role)
            except discord.errors.Forbidden:
                await self.bot.say("Skipping `{}`, permissions error.".format(member))
        await self.bot.say("Giving " + ", ".join(map(str, members)) + " the role {}".format(role))

    @roles.command(name="remove")
    @commands.check(permissions(manage_roles=True))
    async def roles_remove(self, role: discord.Role, *members: discord.Member):
        """
        Removes a role from x members.
        """
        if len(members) == 0:
            await self.bot.say("You need to add a person to remove the role from!")
        await self.bot.say("Removing  the role {} from ".format(role) + ", ".join(map(str, members)))
        for member in members:
            try:
                await self.bot.remove_roles(member, role)
                await asyncio.sleep(.21)
            except discord.errors.Forbidden:
                await self.bot.say("Skipping `{}`, permissions error.".format(member))
        await self.bot.say("Roles removed!")

    @roles.command(name="delete", pass_context=True)
    @commands.check(permissions(manage_roles=True))
    async def roles_delete(self, ctx, *, role: discord.Role):
        """
        Deletes a role from the server.
        """
        server = ctx.message.server
        await self.bot.delete_role(server, role)
        await self.bot.say("Alright, I deleted the role `{}` from the server.".format(role))

    @roles.command(name="color", pass_context=True)
    @commands.check(permissions(manage_roles=True))
    async def roles_color(self, ctx, role: discord.Role, hexcolor: discord.Color):
        """
        Changes the color of a role.
        """
        server = ctx.message.server
        await self.bot.edit_role(server, role, color=hexcolor)
        await self.bot.say("Alright, I changed the role `{}` to the hex color `{}`".format(role, hexcolor))

    @roles.command(name="move", pass_context=True)
    @commands.check(permissions(manage_roles=True))
    async def roles_move(self, ctx, role: discord.Role, position: int):
        """
        Moves a role's position in a server list.
        """
        await self.bot.move_role(ctx.message.server, role, position)
        await self.bot.say("Alright, I moved the role {} to position {}".format(role, position))

    # =============================
    #   Nickname related commands
    # =============================

    @commands.command()
    @commands.check(permissions(manage_server=True))
    async def changenick(self, nickname, *members: discord.Member):
        """
        Changes members nicknames.
        """
        for member in members:
            try:
                await self.bot.change_nickname(member, nickname)
                await self.bot.say("Alright, I changed the nickname of `{}` to `{}`".format(member, nickname))
                await asyncio.sleep(.21)
            except discord.errors.Forbidden:
                await self.bot.say("Skipping `{}`, permissions error.".format(member))

    @commands.command(pass_context=True)
    @commands.check(permissions(manage_server=True))
    async def massnick(self, ctx, *, nickname):
        """
        Mass renames everyone in the server.
        """
        for member in ctx.message.server.members:
            try:
                await self.bot.change_nickname(member, nickname)
                await self.bot.say("Alright, I changed the nickname of `{}` to `{}`".format(member, nickname))
                await asyncio.sleep(.21)
            except discord.errors.Forbidden:
                await self.bot.say("Skipping `{}`, permissions error.".format(member))

    @commands.command(pass_context=True)
    @commands.check(permissions(manage_server=True))
    async def massunnick(self, ctx):
        """
        Mass un-names everyone in the server.
        """
        for member in ctx.message.server.members:
            if member.nick:
                try:
                    await self.bot.change_nickname(member, member.name)
                    await self.bot.say("Alright, I reset the nickname of `{}` to `{}`".format(member, member.name))
                    await asyncio.sleep(.21)
                except discord.errors.Forbidden:
                    await self.bot.say("Skipping `{}`, permissions error.".format(member))


def setup(bot):
    bot.add_cog(Moderation(bot))
