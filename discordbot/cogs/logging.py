"""
Logging.
"""
import asyncio

import discord
from discord.ext import commands
from ghostbin import GhostBin
from sqlalchemy import Column, BIGINT, TEXT
from sqlalchemy.ext.declarative import declarative_base
from yourls import YOURLSClient

from discordbot.bot import DiscordBot
from discordbot.cogs.utils import checks
from discordbot.consts import bot_config

Base = declarative_base()


class Messages(Base):
    __tablename__ = 'Messages'

    guild_id = Column(BIGINT)
    channel_id = Column(BIGINT)
    message_id = Column(BIGINT, primary_key=True)
    author = Column(BIGINT)
    content = Column(TEXT)
    timestamp = Column(TEXT)

    def __repr__(self):
        return "<Messages(guild_id='%s', channel_id='%s', message_id='%s', author='%s', content='%s', timestamp='%s')>" \
               % (self.guild_id, self.channel_id, self.message_id, self.author, self.content, self.timestamp)

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
        if self.bot.logging:
            if "Messages" in self.bot.meta.tables:
                db = self.bot.meta.tables["Messages"]
            else:
                Messages.__table__.create(bind=self.bot.con)
                db = Messages.__table__
            self.db = db

    async def on_message(self, message):
        """
        Process commands and log.
        """
        if message.channel.id not in self.bot.ignored.get("channels"):
            if self.bot.logging:
                db = self.db
                if message.attachments:
                    attachment = " ".join([message.attachments[i]["url"] for i in range(0, len(message.attachments))])
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
                content = message.clean_content.replace("\n", "\x00") + attachment
                author = message.author.id
                message_id = message.id
                time = message.created_at.strftime("%a %B %d %H:%M:%S %Y")
                exc = db.insert().values(guild_id=guild, channel_id=channel, message_id=message_id, author=author,
                                         content=content, timestamp=time)
                await self.bot.loop.run_in_executor(None, self.bot.con.execute, exc)

    async def handle_delete(self, time: int, url: str):
        """
        Deletes a short link.
        """
        yourl = YOURLS(bot_config["bot"]["yourls_base"], signature=bot_config["bot"]["yourls_signature"])
        await asyncio.sleep(time)
        await yourl.delete(url)

    @commands.group(invoke_without_command=True)
    @commands.check(checks.needs_logging)
    async def logs(self, ctx, limit: int = 100):
        """
        Gets the last `x` server logs.
        """
        msgs = []
        counter = 0
        gb = GhostBin()
        server = ctx.message.guild.id if ctx.message.guild else ctx.message.channel.recipient.id
        query = self.bot.sess.query(Messages).filter(Messages.guild_id == server).all()
        if len(query) == 0:
            return await ctx.send("Doesn't look I have a log for this server, sorry!")
        if len(query) < limit:
            limit = len(query)
        for entry in query:
            if counter != limit:
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
            else:
                break
        body = "".join(msgs)
        res = await gb.paste(body, expire="15m")
        if "None" not in [bot_config["bot"]["yourls_base"], bot_config["bot"]["yourls_signature"]]:
            yourl = YOURLS(bot_config["bot"]["yourls_base"], signature=bot_config["bot"]["yourls_signature"])
            res, is_yourl = (await yourl.shorten(res)).shorturl, True
        else:
            res, is_yourl, yourl = res, None, None
        await ctx.send("Here is a link to your logs: {}. Hurry, it expires in 15 minutes!".format(res))
        if is_yourl:
            self.bot.loop.create_task(self.handle_delete(54000, res))

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
        channel = channel if channel else ctx.message.channel
        query = self.bot.sess.query(Messages).filter(Messages.channel_id == channel.id).all()
        if len(query) == 0:
            return await ctx.send("Doesn't look I have a log for that channel, sorry!")
        if len(query) < limit:
            limit = len(query)
        for entry in query:
            if counter != limit:
                user = self.bot.get_user(int(entry.author))
                line = "{} > {}\n".format(str(user), entry.content)
                msgs.append(line)
                counter += 1
            else:
                break
        body = "".join(msgs)
        res = await gb.paste(body, expire="15m")
        if "None" not in [bot_config["bot"]["yourls_base"], bot_config["bot"]["yourls_signature"]]:
            yourl = YOURLS(bot_config["bot"]["yourls_base"], signature=bot_config["bot"]["yourls_signature"])
            res, is_yourl = (await yourl.shorten(res)).shorturl, True
        else:
            res, is_yourl, yourl = res, None, None
        await ctx.send("Here is a link to your logs: {}. Hurry, it expires in 15 minutes!".format(res))
        if is_yourl:
            self.bot.loop.create_task(self.handle_delete(54000, res))

    @logs.command(name="user")
    @commands.check(checks.needs_logging)
    async def logs_user(self, ctx, user: discord.User = None, limit: int = 100):
        """
        Gets the last `x` user logs.
        """
        msgs = []
        counter = 0
        gb = GhostBin()
        user = user if user else ctx.message.author
        query = self.bot.sess.query(Messages).filter(Messages.author == user.id).all()
        if len(query) == 0:
            return await ctx.send("Doesn't look I have a log for that user, sorry!")
        if len(query) < limit:
            limit = len(query)
        for entry in query:
            if counter != limit:
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
            else:
                break
        body = "".join(msgs)
        res = await gb.paste(body, expire="15m")
        if "None" not in [bot_config["bot"]["yourls_base"], bot_config["bot"]["yourls_signature"]]:
            yourl = YOURLS(bot_config["bot"]["yourls_base"], signature=bot_config["bot"]["yourls_signature"])
            res, is_yourl = (await yourl.shorten(res)).shorturl, True
        else:
            res, is_yourl, yourl = res, None, None
        await ctx.send("Here is a link to your logs: {}. Hurry, it expires in 15 minutes!".format(res))
        if is_yourl:
            self.bot.loop.create_task(self.handle_delete(54000, res))


def setup(bot: DiscordBot):
    bot.add_cog(Logging(bot))
