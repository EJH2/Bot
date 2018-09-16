# encoding: utf-8
"""
PrivateBin pasting for the bot

privatebin.py: uploads text to privatebin
using code from <https://github.com/r4sas/PBinCLI/blob/master/pbincli/actions.py>,
© 2017–2018 R4SAS <r4sas@i2pmail.org>
using code from <https://github.com/khazhyk/dango.py/blob/master/dango/zerobin.py>,
© 2017 khazhyk
modified by https://github.com/bmintz
© 2018 bmintz
"""

import asyncio
import base64
import json
import os
import sys
import zlib

import aiohttp
from sjcl import SJCL


def _encrypt(text):
    """
    Supplies encrypted text for the payload.
    """
    key = base64.urlsafe_b64encode(os.urandom(32))
    # Encrypting text
    encrypted_data = SJCL().encrypt(_compress(text.encode('utf-8')), key, mode='gcm')
    return encrypted_data, key


def _compress(s: bytes):
    """
    Compresses bytes for the payload.
    """
    co = zlib.compressobj(wbits=-zlib.MAX_WBITS)
    b = co.compress(s) + co.flush()

    return base64.b64encode(''.join(map(chr, b)).encode())


def _make_payload(text, expires, formatter):
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

    cipher, key = _encrypt(text)
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


async def upload(text, expires, formatter='markdown', server='https://privatebin.net/', loop=None):
    """
    Uploads text to https://privatebin.net
    """
    loop = loop or asyncio.get_event_loop()

    await lock.acquire()
    result = None
    payload, key = await loop.run_in_executor(None, _make_payload, text, expires, formatter)
    python_version = '.'.join(map(str, sys.version_info[:3]))
    async with aiohttp.ClientSession(headers={
        'User-Agent': 'privatebin.py/0.0.2 aiohttp/%s python/%s' % (aiohttp.__version__, python_version),
        'X-Requested-With': 'JSONHttpRequest'
    }) as session:
        for tries in range(2):
            async with session.post(server, data=payload) as resp:
                resp_json = await resp.json()
                if resp_json['status'] == 0:
                    result = _url(server, resp_json['id'], key)
                    break
                elif resp_json['status'] == 1:  # rate limited
                    await asyncio.sleep(10)

    lock.release()

    if result is None:
        raise PrivateBinException('Failed to upload to privatebin')
    else:
        return result


def _url(server, paste_id, key):
    """
    Returns paste url.
    """
    return '%s/?%s#%s' % (server, paste_id, key.decode('utf-8'))
