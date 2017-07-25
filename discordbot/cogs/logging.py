"""
Logging.
"""
import json

import discord
from discord.ext import commands
from ghostbin import GhostBin
from yourls import YOURLSClient

from discordbot.bot import DiscordBot
from discordbot.cogs.utils import checks
from discordbot.cogs.utils.tables import Messages, Table
from discordbot.consts import bot_config


class YOURLS(YOURLSClient):
    async def delete(self, short):
        """
        Deletes a YOURL link.
        """
        data = dict(action='delete', shorturl=short)
        await self._api_request(params=data)


class Logging:
    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.db = bot.db
        self.db.bind_tables(Table)

    # ======================
    #    Logging Messages
    # ======================

    async def on_message(self, message):
        """
        Process commands and log.
        """
        if message.channel.id not in self.bot.ignored.get("channels"):
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
            content = message.clean_content + attachment
            author = message.author.id
            message_id = message.id
            time = message.created_at.strftime("%a %B %d %H:%M:%S %Y")
            values = {"guild_id": guild, "channel_id": channel, "message_id": message_id, "author": author,
                      "content": content, "timestamp": time}
            async with self.bot.db.get_session() as s:
                await s.add(Messages(**values))

    # =========================
    #    Retrieving Messages
    # =========================

    @staticmethod
    async def on_handle_delete(timer):
        """
        Deletes a short link.
        """
        url = json.loads(timer.extras)["url"]
        yourl = YOURLS(bot_config["yourls"]["yourls_base"], signature=bot_config["yourls"]["yourls_signature"])
        await yourl.delete(url)

    async def paste_logs(self, ctx, gb, body):
        res = await gb.paste(body, expire="15m")
        if "None" not in [bot_config["yourls"]["yourls_base"], bot_config["yourls"]["yourls_signature"]]:
            yourl = YOURLS(bot_config["yourls"]["yourls_base"], signature=bot_config["yourls"]["yourls_signature"])
            res, is_yourl = (await yourl.shorten(res)).shorturl, True
        else:
            res, is_yourl, yourl = res, None, None
        await ctx.send("Here is a link to your logs: {}. Hurry, it expires in 15 minutes!".format(res))
        if is_yourl:
            extras = json.dumps({"url": res})
            self.bot.loop.create_task(self.bot.get_cog("Scheduling").create_timer({"expires": 62, "event":
                "handle_delete", "extras": extras}))

    @commands.group(invoke_without_command=True)
    @commands.check(checks.needs_logging)
    async def logs(self, ctx, limit: int = 100):
        """
        Gets the last `x` server logs.
        """
        msgs = []
        counter = 0
        gb = GhostBin()
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
            destination = "{} > {}".format("#" + channel if pm else channel, str(user))
            line = "{} > {}\n".format(destination, entry.content)
            msgs.append(line)
            counter += 1
        body = "".join(msgs)
        await self.paste_logs(ctx, gb, body)

    @logs.command(name="channel")
    @commands.check(checks.needs_logging)
    @commands.guild_only()
    async def logs_channel(self, ctx, channel: discord.TextChannel = None, limit: int = 100):
        """
        Gets the last `x` channel logs.
        """
        msgs = []
        counter = 0
        gb = GhostBin()
        channel = channel if channel else ctx.channel
        async with self.bot.db.get_session() as s:
            query = await s.select(Messages).where(Messages.channel_id == channel.id).limit(limit).all()
            query = await query.flatten()
        if len(query) == 0:
            return await ctx.send("Doesn't look I have a log for that channel, sorry!")
        for entry in list(reversed(query)):
            user = self.bot.get_user(int(entry.author))
            line = "{} > {}\n".format(str(user), entry.content)
            msgs.append(line)
            counter += 1
        body = "".join(msgs)
        await self.paste_logs(ctx, gb, body)

    @logs.command(name="user")
    @commands.check(checks.needs_logging)
    async def logs_user(self, ctx, user: discord.User = None, limit: int = 100):
        """
        Gets the last `x` user logs.
        """
        msgs = []
        counter = 0
        gb = GhostBin()
        user = user if user else ctx.author
        async with self.bot.db.get_session() as s:
            query = await s.select(Messages).where(Messages.author == user.id).limit(limit).all()
            query = await query.flatten()
        if len(query) == 0:
            return await ctx.send("Doesn't look I have a log for that user, sorry!")
        for entry in list(reversed(query)):
            user = self.bot.get_user(int(entry.author))
            if not isinstance(ctx.channel, discord.abc.PrivateChannel):
                channel = self.bot.get_channel(int(entry.channel_id)).name
                pm = False
            else:
                channel = "Private Message with {}".format(str(user))
                pm = True
            destination = "{} > {}".format("#" + channel if pm else channel, str(user))
            line = "{} > {}\n".format(destination, entry.content)
            msgs.append(line)
            counter += 1
        body = "".join(msgs)
        await self.paste_logs(ctx, gb, body)


def setup(bot: DiscordBot):
    bot.add_cog(Logging(bot))
