"""
Bot exceptions.
"""
from discord.ext.commands import CommandError


class ClearanceError(CommandError):
    pass


class Ignored(CommandError):
    pass
