"""
Logging.
"""
import asyncio
import io
import os
import re
from datetime import datetime

import discord
from discord.ext import commands
from ghostbin import GhostBin
from yourls import YOURLSClient

from discordbot.bot import DiscordBot
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

    def message_db(self, message):
        """
        Handles message database storage.
        """
        server_id = str(message.guild.id) or "pm"
        path = "discordbot/cogs/utils/files/logs/{}.log".format(server_id)
        db = self.bot.file_logger(path)
        return db

    async def on_message(self, message):
        """
        Process commands and log.
        """
        if message.channel.id not in self.bot.ignored.get("channels"):
            if self.bot.logging:
                db = self.message_db(message)
                if message.attachments:
                    if message.clean_content:
                        attachment = " " + message.attachments[0]["url"]
                    else:
                        attachment = message.attachments[0]["url"]
                else:
                    attachment = ""
                if isinstance(message.channel, discord.abc.PrivateChannel):
                    destination = '{0.channel.recipient.id}'.format(message)
                else:
                    destination = '#{0.channel.id}'.format(message)
                content = message.clean_content.replace("\n", "\x00")
                db.info('{1} > {0.author.id} > {2}: {3}{4}'.format(
                    message, destination, datetime.now().strftime("%a %B %d %H:%M:%S %Y"), content, attachment))

    async def handle_delete(self, time: int, url: str):
        """
        Deletes a short link.
        """
        yourl = YOURLS(bot_config["bot"]["yourls_base"], signature=bot_config["bot"]["yourls_signature"])
        await asyncio.sleep(time)
        await yourl.delete(url)

    @commands.group(invoke_without_command=True)
    async def logs(self, ctx, limit: int = 100):
        """
        Gets the last `x` server channel logs.
        """
        msgs = []
        counter = 0
        gb = GhostBin()
        if not isinstance(ctx.channel, discord.abc.PrivateChannel):
            path = "discordbot/cogs/utils/files/logs/{}.log".format(ctx.guild.id)
            if not os.path.exists(path):
                return await ctx.send("Doesn't look I have a log for this server, sorry!")
            with io.open(path, "r", encoding="UTF-8") as log:
                logfile = reversed(log.readlines())
                for line in logfile:
                    if counter != limit:
                        sec = line.split(" > ")
                        channel = self.bot.get_channel(int(sec[0].strip("#")))
                        user = self.bot.get_user(int(sec[1]))
                        destination = "#{} > {}".format(channel.name, str(user))
                        line = "{0} > {1}".format(destination, " > ".join(sec[2:]))
                        msgs.append(line.replace("\x00", "\n"))
                        counter += 1
                    else:
                        break
            body = "".join(msgs)
            res = await gb.paste(body, expire="15m")
        else:
            path = "discordbot/cogs/utils/files/logs/pm.log"
            if not os.path.exists(path):
                return await ctx.send("Doesn't look I have a log for this PM, sorry!")
            with io.open(path, "r", encoding="UTF-8") as log:
                logfile = reversed(log.readlines())
                for line in logfile:
                    if counter != limit:
                        sec = line.split(" > ")
                        user_dm = re.sub("[^0-9]", "", sec[0])
                        if int(user_dm) == ctx.message.author.id:
                            user = self.bot.get_user(int(sec[1]))
                            line = "Private Message with {} > {}".format(str(user), " > ".join(sec[2:]))
                            msgs.append(line.replace("\x00", "\n"))
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
