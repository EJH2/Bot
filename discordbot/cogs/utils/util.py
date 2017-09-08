"""
Utility functions.
"""

import json
import re

import aiohttp
from ghostbin import GhostBin
from yourls import YOURLSClient

from discordbot.consts import bot_config


# ===================
#    YOURLS Things
# ===================

class YOURLS(YOURLSClient):
    async def delete(self, short):
        """
        Deletes a YOURL link.
        """
        data = dict(action='delete', shorturl=short)
        await self._api_request(params=data)


def validate_yourls():
    creds = [bot_config["yourls"]["yourls_base"], bot_config["yourls"]["yourls_signature"]]
    if "None" not in creds:
        yourl = YOURLS(creds[0], signature=creds[1])
        return yourl


# =====================
#    GhostBin Things
# =====================

gb = GhostBin()


def human_unreadable_time(time: str):
    human_regex = re.compile(r"(?:(?P<nanoseconds>\d+)ns)?\s*(?:(?P<microseconds>\d+)us)?\s*(?:(?P<milliseconds>\d+)ms)"
                             r"?\s*(?:(?P<seconds>\d+)s)?\s*(?:(?P<minutes>\d+)m)?\s*(?:(?P<hours>\d+)h)?\s*(?:(?P<days"
                             r">\d+)d)?")
    conversion_times = {"nanoseconds": 0.000000001, "microseconds": 0.000001, "milliseconds": 0.001, "seconds": 1,
                        "minutes": 60, "hours": 3600, "days": 86400}
    match = human_regex.match(time)
    if match.group() is not '':
        group = [i for i in match.groupdict() if match.groupdict()[i] is not None][0]
        return int(match.groupdict()[group]) * conversion_times[group]


async def paste_logs(ctx, body: str, expires: str = None):
    res = await gb.paste(body, expire=expires)
    expires = human_unreadable_time(expires)
    yourl = validate_yourls()
    if yourl:
        res = (await yourl.shorten(res)).shorturl
        if ctx.bot.db:
            extras = json.dumps({"url": res})
            ctx.bot.loop.create_task(ctx.bot.get_cog("Scheduling").create_timer({"expires": expires, "event":
                "handle_delete", "extras": extras}))
        else:
            await ctx.bot.loop.create_task(ctx.bot.get_cog("Scheduling").on_handle_delete(None, expires, res))
    return res


# =================
#    Misc Things
# =================


class Borked(Exception):
    pass


async def get_file(bot, url):
    """
    Get a file from the web using aiohttp.
    """
    async with bot.session.get(url) as get:
        assert isinstance(get, aiohttp.ClientResponse)
        data = await get.read()
        return data


def neatly(entries, colors=""):
    """
    Neatly order text.
    """
    width = max(map(lambda t: len(t[0]), entries))
    output = [f"```{colors}"]
    fmt = "\u200b{0:>{width}}: {1}"
    for name, entry in entries:
        output.append(fmt.format(name, entry, width=width))
    output.append("```")
    return "\n".join(output)
