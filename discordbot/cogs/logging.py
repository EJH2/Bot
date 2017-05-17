"""
Logging.
"""

from datetime import datetime

import discord

from discordbot.bot import DiscordBot


class Logging:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    def message_db(self, message):
        """
        Handles message database storage.
        """
        if message.guild is not None:
            server_id = str(message.guild.id)
        else:
            server_id = "pm"
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
                    destination = 'Private Message with {0.channel.recipient.id}'.format(message)
                else:
                    destination = '#{0.channel.id}'.format(message)
                content = message.clean_content.replace("\n", u"\u2063")
                db.info('{1} > {0.author.id} on {2}: {3}{4}'.format(
                    message, destination, datetime.now().strftime("%a %B %d %H:%M:%S %Y"), content, attachment))


def setup(bot: DiscordBot):
    bot.add_cog(Logging(bot))
