# coding=utf-8
"""Error handling for the bot"""
import sys
import traceback

import discord
from discord.ext import commands
from raven import Client

from bot.main import Bot


class ErrorHandler:
    """Error handling for the bot"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.sentry = self.get_sentry()

    def get_sentry(self):
        """Checks to see if sentry is actually available"""
        _sentry = self.bot.config.get('extras', {}).get('sentry', 'None')
        if _sentry is not None:
            sentry = Client(_sentry, enable_breadcrumbs=False)
            return sentry

    async def on_error(self, event_method):
        """
        Catches non-command errors
        """
        print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
        traceback.print_exc()
        self.sentry.captureException()
        self.bot.logger.warn("Error sent to Sentry!")

    async def on_command_error(self, ctx, e):
        """
        Catch command errors.
        """
        if isinstance(e.__cause__, discord.errors.NotFound):
            return
        elif isinstance(e, commands.errors.CommandNotFound):
            return
        elif isinstance(e, commands.errors.NotOwner):
            await ctx.channel.send(f"\N{CROSS MARK} {e}", delete_after=5)
        elif isinstance(e, discord.errors.Forbidden):
            await ctx.channel.send("\N{NO ENTRY} I don't have permission to perform the action", delete_after=5)
        elif isinstance(e, commands.errors.CommandNotFound):
            return
        elif isinstance(e, commands.errors.NoPrivateMessage):
            await ctx.channel.send("\N{NO ENTRY} That command can not be run in PMs!",
                                   delete_after=5)
            return
        elif isinstance(e, commands.errors.DisabledCommand):
            await ctx.channel.send("\N{NO ENTRY} Sorry, but that command is currently disabled!",
                                   delete_after=5)
        elif isinstance(e, commands.errors.CheckFailure):
            await ctx.channel.send("\N{CROSS MARK} Check failed. You probably don't have "
                                   "permission to do this.", delete_after=5)
        elif isinstance(e, commands.errors.CommandOnCooldown):
            await ctx.channel.send(f"\N{NO ENTRY} {e}", delete_after=5)
        elif isinstance(e, (commands.errors.BadArgument, commands.errors.MissingRequiredArgument)):
            await ctx.channel.send(f"\N{CROSS MARK} Bad argument: {' '.join(e.args)}", delete_after=5)
            formatted_help = await ctx.bot.formatter.format_help_for(ctx, ctx.command)
            for page in formatted_help:
                await ctx.channel.send(page, delete_after=20)
        else:
            await ctx.channel.send("\N{NO ENTRY} An error happened. This has been logged and reported.",
                                   delete_after=5)
            if isinstance(e, commands.errors.CommandInvokeError):
                self.bot.logger.error(''.join(traceback.format_exception(
                    type(e), e.__cause__, e.__cause__.__traceback__)))
            else:
                self.bot.logger.error(''.join(traceback.format_exception(type(e), e, e.__traceback__)))
            if not isinstance(e, commands.errors.CommandError):
                if self.sentry:
                    try:
                        raise e.original if hasattr(e, 'original') else e
                    except:
                        assert isinstance(self.sentry, Client)
                        self.sentry.captureException(data={'message': ctx.message.content}, extra={'ctx': ctx.__dict__,
                                                                                                   'error': e})
                    self.bot.logger.warn("Error sent to Sentry!")

    async def on_command(self, ctx):
        """Event ran every time a command is run"""
        author = ctx.author
        if ctx.guild is not None:
            self.bot.command_logger.info(f"[Shard {ctx.guild.shard_id}] {ctx.guild.name} (ID: {ctx.guild.id}) > "
                                         f"{author} (ID: {author.id}): {ctx.message.clean_content}")
        else:
            self.bot.command_logger.info(f"[Shard 0] Private Messages > {author} (ID: {author.id}):"
                                         f" {ctx.message.clean_content}")

    async def on_command_completion(self, ctx):
        """Event ran every time a command completes successfully"""
        self.bot.commands_used[ctx.command.name] += 1
        if not ctx.guild:
            ctx.guild = "PMs"
        self.bot.commands_used_in[str(ctx.guild)] += 1


def setup(bot: Bot):
    """d"""
    bot.add_cog(ErrorHandler(bot))
