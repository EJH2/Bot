# coding=utf-8
"""Utilities for the bot"""
import aiohttp

from bot.main import Bot
from tabulate import tabulate


async def get_file(bot: Bot, url: str) -> bytes:
    """
    Get a file from the web using aiohttp.

    :param bot: DiscordBot instance to grab session.
    :param url: URL to get file from.
    :return: File bytes.
    """
    async with bot.session.get(url) as get:
        assert isinstance(get, aiohttp.ClientResponse)
        data = await get.read()
        return data


def neatly(entries: dict, colors="") -> str:
    """
    Neatly order text.

    :param entries: Entries to neat-ify.
    :param colors: Markdown code for Discord code blocks.
    :return: Neatened string.
    """
    entries = [[f'{entry}:', entries[entry]] for entry in entries]
    return f"```{colors}\n" \
           f"{tabulate(entries, tablefmt='plain', colalign=('right',))}\n" \
           f"```"
