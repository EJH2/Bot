"""
Utility functions.
"""
import aiohttp


class Borked(Exception):
    pass


async def get_file(url):
    """
    Get a file from the web using aiohttp.
    """
    with aiohttp.ClientSession() as sess:
        async with sess.get(url) as get:
            assert isinstance(get, aiohttp.ClientResponse)
            data = await get.read()
            return data


def neatly(entries, colors=""):
    """
    Neatly order text.
    """
    width = max(map(lambda t: len(t[0]), entries))
    output = ["```{}".format(colors)]
    fmt = "\u200b{0:>{width}}: {1}"
    for name, entry in entries:
        output.append(fmt.format(name, entry, width=width))
    output.append("```")
    return "\n".join(output)


async def download(url, path):
    """
    Download a file to a specified path.
    """
    with aiohttp.ClientSession() as sess:
        async with sess.get(url) as get:
            assert isinstance(get, aiohttp.ClientResponse)
            data = await get.read()
            with open(path, "wb") as f:
                f.write(data)
