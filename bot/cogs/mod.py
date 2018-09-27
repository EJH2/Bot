# coding=utf-8
"""File containing moderation commands for the bot"""
import discord
from discord.ext import commands
from bot.main import Bot

from bot.utils import checks


class Mod:
    """Cog containing moderation commands for the bot"""
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(manage_guild=True)
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
    @checks.has_permissions(kick_members=True)
    @checks.bot_has_permissions(kick_members=True)
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
    @checks.has_permissions(kick_members=True)
    @checks.bot_has_permissions(ban_members=True)
    async def softban(self, ctx, *members: discord.Member, days: int = 7):
        """
        Kicks a member and deletes {days} days of their messages. Defaults to 7.
        """
        softbanned = 0
        for member in members:
            try:
                await ctx.guild.ban(member, delete_message_days=days)
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
    @checks.has_permissions(ban_members=True)
    @checks.bot_has_permissions(ban_members=True)
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
    @checks.has_permissions(ban_members=True)
    @checks.bot_has_permissions(ban_members=True)
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

    @commands.command()
    @commands.guild_only()
    @checks.has_permissions(ban_members=True)
    @checks.bot_has_permissions(ban_members=True)
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

    @commands.command()
    @commands.guild_only()
    @checks.has_permissions(manage_messages=True)
    @checks.bot_has_permissions(manage_messages=True)
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
    @checks.has_permissions(manage_messages=True)
    async def clean(self, ctx):
        """
        Deletes messages from the bot in the last 100 messages of a channel.
        """

        def is_me(m):
            """Checks if the message author is the bot."""
            return m.author == self.bot.user

        deleted = await ctx.channel.purge(limit=100, check=is_me)
        await ctx.send('Deleted {} message(s)'.format(len(deleted)))


def setup(bot: Bot):
    """Setup function for the cog"""
    bot.add_cog(Mod(bot))
