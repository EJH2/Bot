# coding=utf-8
"""
URL shortening with Polr for the bot

Uses modified code from
<https://github.com/fauskanger/mypolr/blob/fc11df734e35a1c1d5382341c09c043433c8a851/mypolr/polr_api.py>,
© 2017 Thomas Fauskanger
"""
import aiohttp


def _get_ending(lookup_url: str, api_base: str):
    """
    Returns the short url ending from a short url or an short url ending.
    """
    if lookup_url.startswith(api_base):
        return lookup_url[len(api_base) + 1:]
    return lookup_url


async def shorten(long_url: str, api_base: str, api_key: str):
    """
    Creates a short url if valid.
    """
    params = {
        'url': long_url,
        'key': api_key,
        'response_type': 'json'
    }
    async with aiohttp.ClientSession() as sess:
        async with sess.get(api_base + '/api/v2/action/shorten', params=params) as r:
            data = await r.json()
            action = data.get('action')
            short_url = data.get('result')
            if action == 'shorten' and short_url is not None:
                return short_url


async def lookup(lookup_url: str, api_base: str, api_key: str):
    """
    Looks up the url_ending to obtain information about the short url.
    If it exists, the API will return a dictionary with information, including
    the long_url that is the destination of the given short url URL.
    """
    url_ending = _get_ending(lookup_url, api_base)
    params = {
        'url_ending': url_ending,
        'key': api_key,
        'response_type': 'json'
    }
    async with aiohttp.ClientSession() as sess:
        async with sess.get(api_base + '/api/v2/action/lookup', params=params) as r:
            data = await r.json()
            action = data.get('action')
            full_url = data.get('result')
            if action == 'lookup' and full_url is not None:
                return full_url


async def delete(short_url: str, api_base: str, api_key: str):
    """
    Deletes a short url.
    """
    params = {
        'key': api_key,
        'response_type': 'json'
    }
    url_ending = _get_ending(short_url, api_base)
    async with aiohttp.ClientSession() as sess:
        async with sess.get(api_base + f'/api/v2/links/{url_ending}', params=params) as r:
            data = await r.json()
            if data['message'] == 'OK':
                return True
