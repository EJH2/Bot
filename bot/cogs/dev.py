# coding=utf-8
"""d"""
from discord.ext import commands

from bot.main import Bot


class Dev:
    """d"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def dev(self, ctx, message: int):
        """d"""
        raise RuntimeError(message)


def setup(bot: Bot):
    """d"""
    bot.add_cog(Dev(bot))
