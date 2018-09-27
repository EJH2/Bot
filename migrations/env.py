"""
Example environment file for asql-migrate.
"""
import os
import sys
import typing

from asyncqlio.db import DatabaseInterface
from asyncqlio.orm.session import Session
from ruamel import yaml

sys.path.insert(0, os.path.abspath("."))

with open("config.yaml") as config:
    config = yaml.safe_load(config)

# If you need to import your own tables, do so here.
# import sys, os
# sys.path.insert(0, os.path.abspath("."))
# import my_package.Table

# The DSN to connect to the server with.
# You probably want to change this.
dsn = 'postgresql://{}:{}@{}:{}/{}'
dsn = dsn.format(config["postgres"]["pg_user"], config["postgres"]["pg_pass"], 'localhost', '5432',
                 config["postgres"]["pg_name"])


async def create_database_interface() -> DatabaseInterface:
    """
    Creates the database interface used by the migrations.
    """
    # If you wish to override how the database interface is created, do so here.
    # This includes importing your Table object, and binding tables.
    if dsn is None:
        raise RuntimeError("No DSN provided! Either edit it in env.py, or provide it on the "
                           "command line.")

    db = DatabaseInterface(dsn=dsn)
    await db.connect()
    return db


sig = typing.Callable[[Session], None]


async def run_migration_online(sess: Session, upgrade: sig):
    """
    Runs a migration file "online". This will acquire a session, call the upgrade function, 
    and then commit the session.
    """
    await upgrade(sess)


async def run_migration_offline(sess: Session, upgrade: sig):
    """
    Runs a migration file "offline". 
    """
