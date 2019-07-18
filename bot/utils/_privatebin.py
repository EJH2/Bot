# coding=utf-8
"""
PrivateBin pasting for the bot

privatebin.py: uploads text to privatebin
using code from <https://github.com/r4sas/PBinCLI/blob/master/pbincli/actions.py>,
© 2017–2018 R4SAS <r4sas@i2pmail.org>
using code from <https://github.com/khazhyk/dango.py/blob/master/dango/zerobin.py>,
© 2017 khazhyk
modified by https://github.com/bmintz
© 2018 bmintz
modified by https://github.com/EJH2
© 2019 EJH2
"""

import asyncio
import json
import sys

import aiohttp

from bot.utils.sjcl_helper import encrypt, decrypt


def _make_payload(text: str, expires: str, formatter: str, password: str):
    """
    Creates the payload to be sent to PrivateBin.
    """
    # Formatting request
    request = dict(
        expire=expires,
        formatter=formatter,
        burnafterreading='0',
        opendiscussion='0',
    )

    cipher, key = encrypt(text, password)
    for k in ['salt', 'iv', 'ct']:
        cipher[k] = cipher[k].decode()

    request['data'] = json.dumps(cipher, ensure_ascii=False, default=lambda x: x.decode('utf-8'))
    return request, key


lock = asyncio.Lock()


class PrivateBinException(Exception):
    """
    Default PrivateBin exception.
    """
    pass


async def upload(text: str, expires: str, password: str = None, formatter: str = 'plaintext',
                 server: str = 'https://privatebin.net/', loop=None):
    """
    Uploads text to a https://privatebin.net instance.
    """
    loop = loop or asyncio.get_event_loop()

    await lock.acquire()
    result = None
    payload, key = await loop.run_in_executor(None, _make_payload, text, expires, formatter, password)
    python_version = '.'.join(map(str, sys.version_info[:3]))
    async with aiohttp.ClientSession(headers={
        'User-Agent': 'privatebin.py/0.1.3 aiohttp/%s python/%s' % (aiohttp.__version__, python_version),
        'X-Requested-With': 'JSONHttpRequest'
    }) as session:
        for tries in range(2):
            async with session.post(server, data=payload) as resp:
                resp_json = await resp.json()
                if resp_json['status'] == 0:
                    result = _to_url(server, resp_json['id'], key)
                    break
                elif resp_json['status'] == 1:  # rate limited
                    await asyncio.sleep(10)

    lock.release()

    if result is None:
        raise PrivateBinException('Failed to upload to privatebin')
    else:
        return result


async def get(url: str, password: str = None):
    """
    Gets a paste from a https://privatebin.net instance.
    """

    await lock.acquire()
    result = None
    server, paste_id, passphrase = _from_url(url)
    python_version = '.'.join(map(str, sys.version_info[:3]))
    async with aiohttp.ClientSession(headers={
        'User-Agent': 'privatebin.py/0.1.3 aiohttp/%s python/%s' % (aiohttp.__version__, python_version),
        'X-Requested-With': 'JSONHttpRequest'
    }) as session:
        for tries in range(2):
            async with session.get(_to_url(server, paste_id)) as _get:
                resp_json = await _get.json()
                if resp_json['status'] == 0:
                    data = json.loads(resp_json['data'])
                    result = decrypt(data, passphrase, password)
                elif resp_json['status'] == 1:  # rate limited
                    await asyncio.sleep(10)

    lock.release()

    if result is None:
        raise PrivateBinException('Failed to download from privatebin')
    else:
        return result


def _to_url(server: str, paste_id: str, key: bytes = None):
    """
    Returns paste url.
    """
    if key:
        return '%s/?%s#%s' % (server, paste_id, key.decode('utf-8'))
    return '%s/?%s' % (server, paste_id)


def _from_url(url: str):
    """
    Returns data from paste url.
    """
    server = url.split('?')[0]
    paste_id, key = (url.split('?')[1]).split('#')
    return server, paste_id, key.encode('utf-8')
