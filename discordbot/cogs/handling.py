"""
Command handling for the bot.
"""
import asyncio
import sys
import traceback

import discord
from discord.ext import commands
from raven import Client

from discordbot.main import DiscordBot
from discordbot.utils import exceptions


class CommandHandler:
    """
    Command handling for the bot.
    """

    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.sentry = self.get_sentry()

    async def __global_check(self, ctx):

        author = ctx.author
        if await self.bot.is_owner(ctx.author):
            return True

        # user is a bot
        if author.bot:
            return False

        # user is blacklisted
        if author.id in self.bot.ignored.get("users"):
            return False

        perms = ctx.channel.permissions_for(author)
        perm_list = [perms.administrator, perms.manage_messages, perms.manage_guild]
        un_ignore = any(x for x in perm_list)

        # now we can finally realise if we can actually bypass the ignore
        if not un_ignore and ctx.channel.id in self.bot.ignored.get("channels"):
            raise exceptions.Ignored

        return True

    def get_sentry(self):
        if self.bot.config["sentry"] is not None:
            sentry = Client(self.bot.config["sentry"], enable_breadcrumbs=False)
            return sentry

    async def on_message_edit(self, before, after):
        """
        Checks message edit to see if I screwed up a command...
        """
        await self.bot.process_commands(after)

    async def on_error(self, event_method):
        """
        Catches non-command errors
        """
        print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
        traceback.print_exc()
        self.sentry.captureException()
        self.bot.logger.warn("Error sent to Sentry!")

    async def on_command_error(self, ctx, error):
        """
        Catch command errors.
        """
        if isinstance(error, exceptions.Ignored):
            await ctx.channel.send("\N{CROSS MARK} This channel is currently being ignored.", delete_after=5)
        elif isinstance(error, commands.errors.NotOwner):
            await ctx.channel.send(f"\N{CROSS MARK} {error}", delete_after=5)
        elif isinstance(error, discord.errors.Forbidden):
            await ctx.channel.send("\N{NO ENTRY} I don't have permission to perform the action", delete_after=5)
        elif isinstance(error, exceptions.ClearanceError):
            await ctx.channel.send(f"\N{NO ENTRY} {error}", delete_after=5)
        elif isinstance(error, commands.errors.CommandNotFound):
            return
        elif isinstance(error.__cause__, discord.errors.NotFound):
            return
        elif isinstance(error, exceptions.EmbedError):
            await ctx.channel.send("\N{NO ENTRY} This command requires the `Embed Links` "
                                   "permission to execute!", delete_after=5)
        elif isinstance(error, commands.errors.NoPrivateMessage):
            await ctx.channel.send("\N{NO ENTRY} That command can not be run in PMs!",
                                   delete_after=5)
            return
        elif isinstance(error, commands.errors.DisabledCommand):
            await ctx.channel.send("\N{NO ENTRY} Sorry, but that command is currently disabled!",
                                   delete_after=5)
        elif isinstance(error, commands.errors.CheckFailure):
            await ctx.channel.send("\N{CROSS MARK} Check failed. You probably don't have "
                                   "permission to do this.", delete_after=5)
        elif isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.channel.send(f"\N{NO ENTRY} {error}", delete_after=5)
        elif isinstance(error, (commands.errors.BadArgument, commands.errors.MissingRequiredArgument)):
            await ctx.channel.send(f"\N{CROSS MARK} Bad argument: {' '.join(error.args)}", delete_after=5)
            formatted_help = await ctx.bot.formatter.format_help_for(ctx, ctx.command)
            for page in formatted_help:
                await ctx.channel.send(page, delete_after=20)
        else:
            await ctx.channel.send("\N{NO ENTRY} An error happened. This has been logged and reported.",
                                   delete_after=5)
            if isinstance(error, commands.errors.CommandInvokeError):
                traceback.print_exception(type(error), error.__cause__, error.__cause__.__traceback__, file=sys.stderr)
            else:
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            if self.sentry:
                try:
                    raise error.original
                except:
                    assert isinstance(self.sentry, Client)
                    self.sentry.captureException(data={'message': ctx.message.content}, extra={'ctx': ctx.__dict__,
                                                                                               'error': error})
            self.bot.logger.warn("Error sent to Sentry!")

    async def on_command(self, ctx):
        author = ctx.author
        if ctx.guild is not None:
            self.bot.command_logger.info(f"[Shard {ctx.guild.shard_id}] {ctx.guild.name} (ID: {ctx.guild.id}) > "
                                         f"{author} (ID: {author.id}): {ctx.message.clean_content}")
        else:
            self.bot.command_logger.info(f"[Shard 0] Private Messages > {author} (ID: {author.id}):"
                                         f" {ctx.message.clean_content}")

    async def on_command_completion(self, ctx):
        self.bot.commands_used[ctx.command.name] += 1
        if not ctx.guild:
            ctx.guild = "PMs"
        self.bot.commands_used_in[str(ctx.guild)] += 1
        await asyncio.sleep(5)
        try:
            await ctx.message.delete()
        except discord.DiscordException:
            pass


def setup(bot: DiscordBot):
    bot.add_cog(CommandHandler(bot))
