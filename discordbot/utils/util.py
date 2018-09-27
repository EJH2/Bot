"""
Bot utilities.
"""
import aiohttp

from discordbot.main import DiscordBot


async def get_file(bot: DiscordBot, url: str) -> bytes:
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


def neatly(entries, colors="") -> str:
    """
    Neatly order text.

    :param entries: Entries to neat-ify.
    :param colors: Markdown code for Discord code blocks.
    :return: Neatened string.
    """
    width = max(map(lambda t: len(t[0]), entries))
    output = [f"```{colors}"]
    fmt = "\u200b{0:>{width}}: {1}"
    for name, entry in entries:
        output.append(fmt.format(name, entry, width=width))
    output.append("```")
    return "\n".join(output)
