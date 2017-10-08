"""
Bot utilities.
"""
import re

import aiohttp

from discordbot.main import DiscordBot


# =================
#    Time Things
# =================


def human_unreadable_time(time: str) -> int:
    """
    Convert `60m` to 3600 etc.

    :param time: Human readable time to convert.
    :return: None
    """
    human_regex = re.compile(r"(?:(?P<nanoseconds>\d+)ns)?\s*(?:(?P<microseconds>\d+)us)?\s*(?:(?P<milliseconds>\d+)ms)"
                             r"?\s*(?:(?P<seconds>\d+)s)?\s*(?:(?P<minutes>\d+)m)?\s*(?:(?P<hours>\d+)h)?\s*(?:(?P<days"
                             r">\d+)d)?")
    conversion_times = {"nanoseconds": 0.000000001, "microseconds": 0.000001, "milliseconds": 0.001, "seconds": 1,
                        "minutes": 60, "hours": 3600, "days": 86400}
    match = human_regex.match(time)
    if match.group() is not '':
        group = [i for i in match.groupdict() if match.groupdict()[i] is not None][0]
        return int(match.groupdict()[group]) * conversion_times[group]


# =================
#    Misc Things
# =================


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
