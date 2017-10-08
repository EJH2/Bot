"""
Moderation commands.
"""

import asyncio

import aiohttp
import discord
from discord.ext import commands

from discordbot.main import DiscordBot
from discordbot.utils import tables
from discordbot.utils.checks import permissions


# noinspection PyTypeChecker
class Moderation:
    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.db = bot.db

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
        raise commands.BadArgument(f"Invalid subcommand passed: {ctx.subcommand_passed}")

    @ignore.command(name="list")
    @commands.guild_only()
    async def ignore_list(self, ctx):
        """
        Grabs a list of currently ignored channels in the server.
        """
        if not self.db:
            return await ctx.send("Database is down, try again later?")
        ignored = self.bot.ignored.get("channels", [])
        channel_ids = set(c.id for c in ctx.guild.channels)
        result = []
        for channel in ignored:
            if channel in channel_ids:
                result.append(f"<#{channel}>")

        if result:
            await ctx.send(f"The following channels are ignored:\n\n{', '.join(result)}", delete_after=5)
        else:
            await ctx.send("I am not ignoring any channels here.", delete_after=5)

    @ignore.command(name="channel")
    @commands.check(permissions(manage_channels=True))
    async def ignore_channel(self, ctx, *, channel: discord.TextChannel = None):
        """Ignores a specific channel from being read by the bot.

        If you don"t specify a channel the current channel will be ignored.
        To use this you need Manage Channels.
        """
        if not self.db:
            return await ctx.send("Database is down, try again later?")
        if channel is None:
            channel = ctx.channel

        ignored = self.bot.ignored.get("channels", [])
        if channel.id in ignored:
            await ctx.send("That channel is already ignored.", delete_after=5)
            return

        ignored.append(channel.id)
        values = {"object_id": channel.id, "type": "channel"}
        async with self.db.get_session() as s:
            await s.add(tables.Ignored(**values))
        self.bot.ignored["channels"] = ignored
        await ctx.send("I am no longer reading from that channel.", delete_after=5)

    @ignore.command(name="server")
    @commands.check(permissions(manage_server=True))
    async def ignore_server(self, ctx):
        """Ignores the whole server from the bot.

        To use this you need Manage Server.
        """
        if not self.db:
            return await ctx.send("Database is down, try again later?")
        ignored = self.bot.ignored.get("channels", [])
        channels_ = ctx.guild.channels
        channels = [c.id for c in channels_ if c.type == discord.ChannelType.text]
        ignored.extend(channels)

        rows = []
        for chan in channels:
            values = {"object_id": chan.id, "type": "channel"}
            rows.append(tables.Ignored(**values))
        async with self.db.get_session() as s:
            await s.insert.rows(*rows)
        self.bot.ignored["channels"] = list(set(ignored))  # make unique
        await ctx.send("I am now ignoring this server.", delete_after=5)

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @commands.check(permissions(manage_channels=True))
    async def unignore(self, ctx):
        """
        Command for un-ignoring channels/the server.
        """
        raise commands.BadArgument(f"Invalid subcommand passed: {ctx.subcommand_passed}")

    @unignore.command(name="channel")
    @commands.guild_only()
    @commands.check(permissions(manage_channels=True))
    async def unignore_channel(self, ctx, channel: discord.TextChannel = None):
        """Unignores channels from being read by the bot.

        If no channels are specified, it unignores the current channel.
        To use this you need Manage Channels.
        """
        if not self.db:
            return await ctx.send("Database is down, try again later?")
        if not channel:
            channel = ctx.channel

        # a set is the proper data type for the ignore list
        # however, JSON only supports arrays and objects not sets.
        ignored = self.bot.ignored.get("channels", [])
        if channel.id not in ignored:
            await ctx.send("I am not currently ignoring that channel.", delete_after=5)
            return

        async with self.db.get_session() as s:
            query = await s.select(tables.Ignored).where(tables.Ignored.object_id == channel.id).first()
            await s.remove(query)
        self.bot.ignored["channels"].remove(channel.id)
        await ctx.send("I am now reading from that channel.", delete_after=5)

    @unignore.command(name="server")
    @commands.guild_only()
    @commands.check(permissions(manage_server=True))
    async def unignore_server(self, ctx):
        """
        Un-ignores all channels in this server from being read by the bot.

        To use this you need Manage Server.
        """
        if not self.db:
            return await ctx.send("Database is down, try again later?")
        channels = [c for c in ctx.guild.channels if c.type is discord.channel.ChannelType.text]
        ignored = self.bot.ignored.get("channels", [])
        for channel in channels:
            try:
                ignored.remove(channel.id)
            except ValueError:
                pass
            async with self.db.get_session() as s:
                query = await s.select(tables.Ignored).where(tables.Ignored.object_id == channel.id).first()
                if query is not None:
                    await s.remove(query)
                    self.bot.ignored["channels"] = ignored

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
        bans = await ctx.guild.bans()
        if len(bans) == 0:
            await ctx.send("There are no active bans currently on the server.")
        else:
            await ctx.send(f"The currently active bans for this server are: {', '.join(map(str, bans))}")

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(kick_members=True))
    async def kick(self, ctx, *members: discord.Member):
        """
        Kicks the member of choice.
        """
        for member in members:
            try:
                await ctx.guild.kick(member)
                await ctx.send(f"{member.name} was kicked from the server.")
            except discord.errors.Forbidden:
                await ctx.send(f"Skipping `{member}`, permissions error.")

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(kick_members=True))
    async def softban(self, ctx, *members: discord.Member):
        """
        Kicks a member and deletes 7 days of their messages.
        """
        softbanned = 0
        for member in members:
            try:
                await ctx.guild.ban(member, delete_message_days=7)
                await ctx.guild.unban(member)
                softbanned += 1
            except discord.errors.DiscordException as e:
                try:
                    await ctx.send(f"User `{str(member)}` (ID: `{member.id}`) could not be softbanned: `{e}`")
                except discord.errors.DiscordException as err:
                    await ctx.send(f"User `{member}` could not be softbanned: `{err}`")
        await ctx.send(f"Successfully softbanned {softbanned}/{len(members)} users")

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(ban_members=True))
    async def ban(self, ctx, *members: discord.Member):
        """
        Bans a member and deletes their messages.
        """
        banned = 0
        for member in members:
            try:
                await ctx.guild.ban(member, delete_message_days=7)
                banned += 1
            except discord.errors.DiscordException as e:
                try:
                    await ctx.send(f"User `{str(member)}` (ID: `{member.id}`) could not be banned: `{e}`")
                except discord.errors.DiscordException as err:
                    await ctx.send(f"User `{member}` could not be banned: `{err}`")
        await ctx.send(f"Successfully banned {banned}/{len(members)} users")

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(ban_members=True))
    async def unban(self, ctx, *, name: str):
        """
        Unbans a member.
        """
        bans = await ctx.guild.bans()
        member = discord.utils.get(bans, user__name=name)
        if member:
            await ctx.guild.unban(member.user)
            await ctx.send(f"{str(member.user)} has been unbanned from the server!")
            return
        await ctx.send("You can't unban a member that hasn't been banned!")

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @commands.check(permissions(ban_members=True))
    async def hackban(self, ctx, *user_ids: int):
        """
        Preemptive bans a user.
        """
        banned = 0
        for user_id in user_ids:
            try:
                await ctx.guild.ban(discord.Object(id=user_id))
                banned += 1
            except discord.errors.DiscordException as e:
                try:
                    user = await ctx.bot.get_user_info(user_id)
                    await ctx.send(f"User `{str(user)}` (ID: `{user.id}`) could not be banned: `{e}`")
                except discord.errors.DiscordException as err:
                    await ctx.send(f"User `{user_id}` could not be banned: `{err}`")
        await ctx.send(f"Successfully banned {banned}/{len(user_ids)} users")

    @hackban.command()
    @commands.guild_only()
    @commands.check(permissions(ban_members=True))
    async def url(self, ctx, url: str):
        """
        Attempts to ban a list of raw IDs from a raw pastebin link.
        """
        if "https://pastebin.com/raw/" not in url:
            return await ctx.send("The link should look like https://pastebin.com/raw/{Random String}")
        async with self.bot.session.get(url) as get:
            assert isinstance(get, aiohttp.ClientResponse)
            data = await get.read()
            data = data.decode("utf-8").split()
            await ctx.invoke(self.hackban, *data)

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(manage_guild=True, kick_members=True, ban_members=True))
    async def leave(self, ctx):
        """
        Makes me leave the server.
        """
        server = ctx.guild
        await ctx.send("Alright, everyone! I'm off to a new life elsewhere! Until next time! :wave:")
        await server.leave()

    # =========================
    #   Chat related commands
    # =========================

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(manage_messages=True))
    async def prune(self, ctx, messages: int = 100):
        """
        Deletes x amount of messages in a channel.
        """
        if messages > 1000:
            return ctx.send("That's too many messages! 1000 or less please.")
        await ctx.channel.purge(limit=messages + 1)
        removed = messages + 1
        await ctx.send(f"Removed {removed} messages")

    @commands.command()
    @commands.check(permissions(manage_messages=True))
    async def clean(self, ctx):
        """
        Deletes messages from the bot in the last 100 messages of a channel.
        """

        def is_me(m):
            return m.author == self.bot.user

        deleted = await ctx.channel.purge(limit=100, check=is_me)
        await ctx.send('Deleted {} message(s)'.format(len(deleted)))

    # ===========================
    #   Invite related commands
    # ===========================

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def invites(self, ctx):
        """
        Command for server invites.
        """
        raise commands.BadArgument(f"Invalid subcommand passed: {ctx.subcommand_passed}")

    @invites.command(name="create")
    @commands.guild_only()
    async def invites_create(self, ctx, channel: discord.TextChannel = None):
        """
        Creates an instant invite.
        """
        if channel is None:
            channel = ctx.channel
        invite = await channel.create_invite()
        await ctx.send(invite)

    @invites.command(name="delete")
    @commands.guild_only()
    @commands.check(permissions(manage_server=True))
    async def invites_delete(self, ctx, invite: discord.Invite):
        """
        Deletes/Deactivates an invite.
        """
        if invite.guild != ctx.guild:
            return await ctx.send("You can't delete invites from other guilds!")
        await self.bot.delete_invite(invite)
        await ctx.send("Successfully deleted the invite!")

    @invites.command(name="list")
    @commands.guild_only()
    @commands.check(permissions(manage_server=True))
    async def invites_list(self, ctx):
        """
        Lists the currently active invites on the server.
        """
        invs = await ctx.guild.invites()
        if len(invs) == 0:
            await ctx.send("There are no active invites currently on the server.")
        else:
            await ctx.send(f"The currently active invites for this server are: {', '.join(map(str, invs))}")

    @invites.command(name="check")
    async def invites_check(self, ctx, invite: discord.Invite):
        """
        Gives information about a discord invite link.
        """
        invite.max_age = invite.max_age if invite.max_age is not None else 0
        m, s = divmod(invite.max_age, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        w, d = divmod(d, 7)
        em = discord.Embed(title=f"Info for Invite {invite.code}:")
        em.set_thumbnail(url=f"https://cdn.discordapp.com/icons/{invite.guild.id}/{invite.guild.icon}.webp")
        em.add_field(name="Guild:", value=f"{invite.guild.name} (ID: {invite.guild.id})", inline=False)
        em.add_field(name="Channel:", value=f"#{invite.channel.name} (ID: {invite.channel.id})", inline=False)
        em.add_field(name="Inviter:", value=f"{invite.inviter.name} (ID: {invite.inviter.id})", inline=False)
        em.add_field(name="Uses:", value=invite.uses, inline=False)
        em.add_field(name="Max Uses:", value=invite.max_uses if invite.max_uses else "Infinite", inline=False)
        em.add_field(name="Expires In:", value=f"{int(w)}w : {int(d)}d : {int(h)}h : {int(m)}m : {int(s)}s" if
        invite.max_age > 0 else "Never")
        await ctx.send(embed=em)

    # =========================
    #   Role related commands
    # =========================

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @commands.check(permissions(manage_roles=True))
    async def roles(self, ctx):
        """
        Command for server roles.
        """
        raise commands.BadArgument(f"Invalid subcommand passed: {ctx.subcommand_passed}")

    @roles.command(name="create")
    @commands.guild_only()
    @commands.check(permissions(manage_roles=True))
    async def roles_create(self, ctx, *, role):
        """
        Creates a server role.
        """
        await ctx.guild.create_role(name=role)
        await ctx.send(f"Alright, I created the role `{role}`")

    @roles.command(name="add")
    @commands.guild_only()
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
                await ctx.send(f"Skipping `{member}`, permissions error.")
        await ctx.send(f"Giving {', '.join(map(str, members))} the role {member}")

    @roles.command(name="remove")
    @commands.guild_only()
    @commands.check(permissions(manage_roles=True))
    async def roles_remove(self, ctx, role: discord.Role, *members: discord.Member):
        """
        Removes a role from x members.
        """
        if len(members) == 0:
            await ctx.send("You need to add a person to remove the role from!")
        await ctx.send(f"Removing  the role `{role}` from {', '.join(map(str, members))}")
        for member in members:
            try:
                await member.remove_roles(role)
                await asyncio.sleep(.21)
            except discord.errors.Forbidden:
                await ctx.send(f"Skipping `{member}`, permissions error.")
        await ctx.send("Roles removed!")

    @roles.command(name="delete")
    @commands.guild_only()
    @commands.check(permissions(manage_roles=True))
    async def roles_delete(self, ctx, *, role: discord.Role):
        """
        Deletes a role from the server.
        """
        await ctx.guild.delete_role(role)
        await ctx.send(f"Alright, I deleted the role `{role}` from the server.")

    @roles.command(name="color")
    @commands.guild_only()
    @commands.check(permissions(manage_roles=True))
    async def roles_color(self, ctx, role: discord.Role, hexcolor: discord.Color):
        """
        Changes the color of a role.
        """
        await ctx.guild.edit_role(role, color=hexcolor)
        await ctx.send(f"Alright, I changed the role `{role}` to the hex color `{hexcolor}`")

    @roles.command(name="move")
    @commands.guild_only()
    @commands.check(permissions(manage_roles=True))
    async def roles_move(self, ctx, role: discord.Role, position: int):
        """
        Moves a role's position in a server list.
        """
        await ctx.guild.move_role(role, position)
        await ctx.send(f"Alright, I moved the role {role} to position {position}")

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
                await ctx.send(f"Alright, I changed the nickname of `{member}` to `{nickname}`")
                await asyncio.sleep(.21)
            except discord.errors.Forbidden:
                await ctx.send(f"Skipping `{member}`, permissions error.")

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(manage_server=True))
    async def massnick(self, ctx, *, nickname):
        """
        Mass renames everyone in the server.
        """
        nicked = 0
        for member in ctx.guild.members:
            try:
                await member.edit(nick=nickname)
                nicked += 1
            except discord.errors.DiscordException as e:
                await ctx.send(f"User `{str(member)}` (ID: `{member.id}`) could not be re-nicked: `{e}`")
        await ctx.send(f"Successfully nicked {nicked}/{len(ctx.guild.members)} users to {nickname}")

    @commands.command()
    @commands.guild_only()
    @commands.check(permissions(manage_server=True))
    async def massunnick(self, ctx):
        """
        Mass un-names everyone in the server.
        """
        unnicked = 0
        for member in ctx.guild.members:
            try:
                await member.edit(nick=None)
                unnicked += 1
            except discord.errors.DiscordException as e:
                await ctx.send(f"User `{str(member)}` (ID: `{member.id}`) could not be re-nicked: `{e}`")
        await ctx.send(f"Successfully unnicked {unnicked}/{len(ctx.guild.members)} users!")


def setup(bot: DiscordBot):
    bot.add_cog(Moderation(bot))
