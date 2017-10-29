"""
Ghostbin handling for the bot.
"""

from ghostbin import GhostBin as Gb

from discordbot.main import DiscordBot


class GhostBin:
    """
    Ghostbin handling for the bot.
    """

    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.ghostbin = Gb()

    async def paste_logs(self, body: str, expires: str = None) -> str:
        res = await self.ghostbin.paste(body, expire=expires)
        return res


def setup(bot: DiscordBot):
    bot.add_cog(GhostBin(bot))
