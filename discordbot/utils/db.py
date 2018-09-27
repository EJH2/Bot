"""
Database utilities.
"""
from asyncqlio import DatabaseInterface


async def connect(user, password, db, host='localhost', port=5432) -> DatabaseInterface:
    """
    Connects to a database.

    :param user: Username for database.
    :param password: Password for database.
    :param db: Database name.
    :param host: Database hostname.
    :param port: Database port.
    :return: Database connection.
    """
    url = f'postgresql://{user}:{password}@{host}:{port}/{db}'

    db = DatabaseInterface(url)
    await db.connect()

    return db
