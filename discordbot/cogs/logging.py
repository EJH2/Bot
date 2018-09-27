"""
Logging/log retrieval for the bot.
"""
import ast
import asyncio

import asyncpg
import discord
from discord.ext import commands

from discordbot.main import DiscordBot
from discordbot.utils import checks
from discordbot.utils.tables import Messages


class Logging:
    """
    Logging/log retrieval for the bot.
    """

    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.gb = bot.get_cog("GhostBin")

    # ======================
    #    Logging Messages
    # ======================

    async def on_message(self, message):
        """
        Process commands and log.
        """
        try:
            if message.channel.id not in self.bot.ignored["channels"]:
                if message.attachments:
                    attachment = " ".join([message.attachments[i].url for i in range(0, len(message.attachments))])
                    if message.clean_content:
                        attachment = " " + attachment
                else:
                    attachment = ""
                if isinstance(message.channel, discord.abc.PrivateChannel):
                    guild = message.channel.recipient.id
                    channel = message.channel.recipient.id
                else:
                    guild = message.guild.id
                    channel = message.channel.id
                content = bytes(message.clean_content + attachment, "utf-8")
                encrypted = str(self.bot.cipher.encrypt(content))
                author = message.author.id
                message_id = message.id
                time = message.created_at
                values = {"guild_id": guild, "channel_id": channel, "message_id": message_id, "author": author,
                          "content": encrypted, "timestamp": time}
                async with self.bot.db.get_session() as s:
                    await s.add(Messages(**values))
        except asyncpg.exceptions.InterfaceError:
            pass

    # =========================
    #    Retrieving Messages
    # =========================

    @commands.group(invoke_without_command=True)
    @commands.check(checks.needs_logging)
    async def logs(self, ctx, limit: int = 100):
        """Gets the last `x` server logs."""
        msgs = []
        counter = 0
        server = ctx.guild.id if ctx.guild else ctx.channel.recipient.id
        async with self.bot.db.get_session() as s:
            query = await s.select(Messages).where(Messages.guild_id == server).limit(limit).all()
            query = await query.flatten()
        if len(query) == 0:
            return await ctx.send("Doesn't look I have a log for this server, sorry!")
        for entry in list(reversed(query)):
            user = self.bot.get_user(int(entry.author))
            if not isinstance(ctx.channel, discord.abc.PrivateChannel):
                channel = self.bot.get_channel(int(entry.channel_id)).name
                pm = False
            else:
                channel = "Private Message with {}".format(str(user))
                pm = True
            destination = f"{'#' + channel if not pm else channel} > {str(user)}"
            content = ast.literal_eval(entry.content)
            decrypted = (self.bot.cipher.decrypt(content)).decode("utf-8")
            line = f"{destination} > {decrypted}\n"
            msgs.append(line)
            counter += 1
        body = "".join(msgs)
        res = await self.gb.paste_logs(body, "15m")
        await ctx.send(f"Here is a link to your logs: {res}. Hurry, it expires in 15 minutes!")

    @logs.command(name="channel")
    @commands.check(checks.needs_logging)
    @commands.guild_only()
    async def logs_channel(self, ctx, channel: discord.TextChannel = None, limit: int = 100):
        """Gets the last `x` channel logs."""
        msgs = []
        counter = 0
        channel = channel if channel else ctx.channel
        async with self.bot.db.get_session() as s:
            query = await s.select(Messages).where(Messages.channel_id == channel.id).limit(limit).all()
            query = await query.flatten()
        if len(query) == 0:
            return await ctx.send("Doesn't look I have a log for that channel, sorry!")
        for entry in list(reversed(query)):
            user = self.bot.get_user(int(entry.author))
            content = ast.literal_eval(entry.content)
            decrypted = (self.bot.cipher.decrypt(content)).decode("utf-8")
            line = f"{str(user)} > {decrypted}\n"
            msgs.append(line)
            counter += 1
        body = "".join(msgs)
        res = await self.gb.paste_logs(body, "15m")
        await ctx.send(f"Here is a link to your logs: {res}. Hurry, it expires in 15 minutes!")

    @logs.command(name="user")
    @commands.check(checks.needs_logging)
    @commands.guild_only()
    async def logs_user(self, ctx, user: discord.User = None, limit: int = 100):
        """Gets the last `x` user logs."""
        msgs = []
        counter = 0
        user = user if user else ctx.author
        async with self.bot.db.get_session() as s:
            query = await s.select(Messages).where(Messages.author == user.id).limit(limit).all()
            query = await query.flatten()
        if len(query) == 0:
            return await ctx.send("Doesn't look I have a log for that user, sorry!")
        for entry in list(reversed(query)):
            user = self.bot.get_user(int(entry.author))
            channel = self.bot.get_channel(int(entry.channel_id)).name
            destination = "{} > {}".format("#" + channel, str(user))
            content = ast.literal_eval(entry.content)
            decrypted = (self.bot.cipher.decrypt(content)).decode("utf-8")
            line = "{} > {}\n".format(destination, decrypted)
            msgs.append(line)
            counter += 1
        body = "".join(msgs)
        res = await self.gb.paste_logs(body, "15m")
        await ctx.send(f"Here is a link to your logs: {res}. Hurry, it expires in 15 minutes!")

    @logs.group(invoke_without_command=True, name="purge")
    @commands.check(checks.needs_logging)
    @commands.is_owner()
    async def logs_purge(self, ctx):
        """Purges all user logs. Only usable by the bot owner."""
        await ctx.send("Are you sure you want to clear *all* entries? This action is IRREVERSIBLE! "
                       "If yes, type `yes` in 10 seconds, or the action will be aborted.")

        def check(m):
            return m.author == ctx.author and m.content.lower() == "yes"

        try:
            await ctx.bot.wait_for("message", check=check, timeout=10)
        except asyncio.TimeoutError:
            return await ctx.send("Timeout limit reached, aborting.")

        async with self.bot.db.get_session() as s:
            await s.truncate(Messages)

        await ctx.send("Purged all messages!")

    @logs_purge.command(name="user")
    @commands.check(checks.needs_logging)
    @commands.is_owner()
    async def logs_purge_user(self, ctx, user: discord.User):
        """Purges the logs of a user to comply with the Discord ToS."""
        await ctx.send(f"Are you sure you want to clear *all* entries for user with ID {user.id}? "
                       f"This action is IRREVERSIBLE! If yes, type `yes` in 10 seconds, or the action will be aborted.")

        def check(m):
            return m.author == ctx.author and m.content.lower() == "yes"

        try:
            await self.bot.wait_for("message", check=check, timeout=10)
        except asyncio.TimeoutError:
            return await ctx.send("Timeout limit reached, aborting.")
        async with self.bot.db.get_session() as s:
            await s.delete(Messages).where(Messages.author == user.id).run()

        await ctx.send(f"Purged all messages from user with ID {user.id}")


def setup(bot: DiscordBot):
    bot.add_cog(Logging(bot))
