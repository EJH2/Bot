# coding=utf-8
"""ArgParse file for bot"""
from discord.ext import commands

from bot.main import Bot
from bot.utils.args import *


class Br:
    """dd"""

    def __init__(self, bot: Bot):
        self.bot = bot

    # Example command:
    @commands.group(aliases=["words", "wc"], invoke_without_command=True)
    async def word_cloud(self, ctx, thinkerton, *, args: ArgParseConverter(
        [Argument("--mask", help="Mask to use", default="mask"),
         Argument("--font", help="Font to use", default="random"),
         Argument("--color", help="Background color"),
         Argument(
             "--count", default=1000, type=int,
             help="Number of messages to use")]) = Default(count=1000, font="random")):
        """d"""
        print(thinkerton, ctx.command.name)
        msg = ctx.message
        args_ = args
        print(msg, args_)
        await ctx.send(args_)

    @word_cloud.command(aliases=["borb", "birb"])
    async def bird_pic(self, ctx, thunk, *, args: ArgParseConverter(
        [Argument("--color", help="Borb color"),
         Argument("--count", default=10, type=int, help="Borb count")]
    ) = Default(count=10, color="red")):
        """d"""
        print(thunk)
        msg = ctx.message
        args_ = args
        print(msg, args_)
        await ctx.send(args_)


def setup(bot: Bot):
    """Setup function for the cog"""
    bot.add_cog(Br(bot))
