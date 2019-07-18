# coding=utf-8
"""Database info for the bot."""
from gino import Gino

db = Gino()


class Users(db.Model):
    """Users table for bot."""
    __tablename__ = 'users'

    id = db.Column(db.BigInteger, primary_key=True, index=True)
    data = db.Column(db.JSON)
    key = db.Column(db.LargeBinary, nullable=False)


class Messages(db.Model):
    """Messages table for bot."""
    __tablename__ = 'messages'

    id = db.Column(db.BigInteger, primary_key=True, index=True)
    data = db.Column(db.JSON)
    key = db.Column(db.LargeBinary, nullable=False)


class Ignored(db.Model):
    """Ignored users/channels"""
    __tablename__ = 'ignored'

    id = db.Column(db.BigInteger, primary_key=True, index=True)
    reason = db.Column(db.VARCHAR, nullable=True)


async def create_engine(**credentials):
    """Create Database connection"""
    bind = 'postgresql://{user}:{password}@{host}:{port}/{db}'.format(**credentials)
    await db.set_bind(bind)
    return db


def sjcl_to_json(encrypted_data: dict):
    """Takes an SJCL payload and converts it to proper JSON"""
    js = dict()
    for k in encrypted_data:
        js[k] = encrypted_data[k]
        if isinstance(encrypted_data[k], bytes):
            js[k] = (encrypted_data[k]).decode()
    return js


def json_to_sjcl(raw_data):
    """Takes data returned from the DB and converts it to something SJCL can read"""
    encrypted_data = dict()
    for k in raw_data:
        encrypted_data[k] = raw_data[k]
        if k in ['salt', 'ct', 'iv']:
            encrypted_data[k] = (raw_data[k]).encode()
    return encrypted_data
