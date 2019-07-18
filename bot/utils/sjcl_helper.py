# coding=utf-8
"""
SJCL utilities for the bots various functions

using code from <https://github.com/r4sas/PBinCLI/blob/master/pbincli/actions.py>,
© 2017–2018 R4SAS <r4sas@i2pmail.org>
using code from <https://github.com/khazhyk/dango.py/blob/master/dango/zerobin.py>,
© 2017 khazhyk
modified by https://github.com/bmintz
© 2018 bmintz
"""
import base64
import hashlib
import os
import zlib

from sjcl import SJCL


def encrypt(text: str, password: str = None):
    """
    Supplies encrypted text for the payload.
    """
    key = base64.urlsafe_b64encode(os.urandom(32))

    if password:
        digest = hashlib.sha256(password.encode()).hexdigest()
        passphrase = key + digest.encode()
    else:
        passphrase = key

    # Encrypting text
    encrypted_data = SJCL().encrypt(_compress(text.encode()), passphrase, mode='gcm')
    return encrypted_data, key


def decrypt(encrypted_data: dict, key: bytes, password: str = None):
    """
    Supplies decrypted text from the payload.
    """
    if password:
        digest = hashlib.sha256(password.encode()).hexdigest()
        passphrase = key + digest.encode()
    else:
        passphrase = key

    # Decrypting text
    data = _decompress(SJCL().decrypt(encrypted_data, passphrase).decode())
    return data


def _compress(s: bytes):
    """
    Compresses bytes for the payload.
    """
    co = zlib.compressobj(wbits=-zlib.MAX_WBITS)
    b = co.compress(s) + co.flush()

    return base64.b64encode(''.join(map(chr, b)).encode())


def _decompress(s: str):
    """
    Decompresses bytes returned from the payload.
    """
    return zlib.decompress(bytearray(map(ord, base64.b64decode(s.encode()).decode('utf-8'))), -zlib.MAX_WBITS).decode()
