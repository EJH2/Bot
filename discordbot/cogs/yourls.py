"""
YOURLS handling for the bot. Most likely, you won't have this, though.
"""
import asyncio
import json

import requests
from yourls import YOURLSClient

from discordbot.main import DiscordBot


class YOURLS_(YOURLSClient):
    async def delete(self, short):
        """
        Deletes a YOURL link.
        """
        data = dict(action='delete', shorturl=short)
        await self._api_request(params=data)


class YOURLS:
    """
    YOURLS handling for the bot. Most likely, you won't have this, though.
    """

    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.yourls = self.validate_yourls()

    def validate_yourls(self) -> [YOURLS_, str]:
        """
        Checks YOURL credentials by sending a GET request to the base URL.

        :return: YOURL class if succeed, None if failed.
        """
        creds = [self.bot.config["yourls"]["yourls_base"], self.bot.config["yourls"]["yourls_signature"]]
        if "None" not in creds:
            with requests.get(f"{creds[0]}?signature={creds[1]}&action=db-stats") as get:
                if get.status_code == 200:
                    yourl = YOURLS_(creds[0], signature=creds[1])
                    return yourl
        return None

    async def create_url(self, url: str) -> str:
        """
        Creates a YOURL shortened URL.

        :param url: The url to be shortened.
        :return: Shortened URL if the user has passed valid YOURL credentials, else URL
        """
        if self.yourls:
            yourls_entry = await self.yourls.shorten(url)
            url = yourls_entry.shorturl
        return url

    async def on_url_delete(self, timer=None, seconds: int = None, url=None):
        """
        Deletes a shortened link.

        :param timer:
        :param seconds:
        :param url:
        :return: None
        """
        if timer:
            url = json.loads(timer.extras)["url"]
            await self.yourls.delete(url)
        else:
            await asyncio.sleep(seconds)
            await self.yourls.delete(url)


def setup(bot: DiscordBot):
    bot.add_cog(YOURLS(bot))
