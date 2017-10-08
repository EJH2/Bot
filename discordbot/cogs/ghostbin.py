"""
Ghostbin handling for the bot.
"""
import json

from ghostbin import GhostBin as Gb

from discordbot.main import DiscordBot
from discordbot.utils import util


class GhostBin:
    """
    Ghostbin handling for the bot.
    """

    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.ghostbin = Gb()

    async def paste_logs(self, body: str, expires: str = None) -> str:
        res = await self.ghostbin.paste(body, expire=expires)
        expires = util.human_unreadable_time(expires)
        yourls = self.bot.get_cog("YOURLS")
        res = await yourls.create_url(res)
        # Due to the fact that `res` could be either a YOURLS link or a Ghostbin link,
        # this makes sure we only schedule a deletion if `res` is a YOURLS link
        if yourls.yourls:
            if self.bot.db:
                extras = json.dumps({"url": res})
                self.bot.loop.create_task(self.bot.get_cog("Scheduling").create_timer({"expires": expires, "event":
                    "url_delete", "extras": extras}))
            else:
                await self.bot.loop.create_task(self.bot.get_cog("YOURLS").on_url_delete(None, expires, res))
        return res


def setup(bot: DiscordBot):
    bot.add_cog(GhostBin(bot))
