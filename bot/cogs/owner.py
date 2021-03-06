# coding=utf-8
"""File containing core commands of the bot"""
import asyncio
import inspect
import io
import textwrap
import traceback
from contextlib import redirect_stdout

import discord
from discord.ext import commands

from bot.main import Bot


# noinspection PyBroadException,PyBroadException,PyBroadException,PyBroadException,PyBroadException,PyBroadException
class Owner:
    """Cog containing core commands of the bot"""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()

    async def __local_check(self, ctx):
        """Check to see if the user running a command from this cog is the owner of the bot"""
        return await self.bot.is_owner(ctx.author)

    @staticmethod
    def cleanup_code(content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @staticmethod
    def get_syntax_error(e):
        """Parses errors into a codeblock for easy reading"""
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @commands.command()
    async def debug(self, ctx, *, body: str):
        """Evaluates a code."""

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @commands.command()
    async def repl(self, ctx):
        """Launches an interactive REPL session."""
        variables = {
            'ctx': ctx,
            'bot': self.bot,
            'message': ctx.message,
            'guild': ctx.guild,
            'channel': ctx.channel,
            'author': ctx.author,
            '_': None,
        }

        if ctx.channel.id in self.sessions:
            await ctx.send('Already running a REPL session in this channel. Exit it with `quit`.')
            return

        self.sessions.add(ctx.channel.id)
        await ctx.send('Enter code to execute or evaluate. `exit()` or `quit` to exit.')

        def check(m):
            """Checks to see if the user running the repl is the same one that initiated it"""
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and m.content.startswith('`')

        while True:
            try:
                response = await self.bot.wait_for('message', check=check, timeout=10.0 * 60.0)
            except asyncio.TimeoutError:
                await ctx.send('Exiting REPL session.')
                self.sessions.remove(ctx.channel.id)
                break

            cleaned = self.cleanup_code(response.content)

            if cleaned in ('quit', 'exit', 'exit()'):
                await ctx.send('Exiting.')
                self.sessions.remove(ctx.channel.id)
                return

            executor = exec
            code = None
            if cleaned.count('\n') == 0:
                # single statement, potentially 'eval'
                try:
                    code = compile(cleaned, '<repl session>', 'eval')
                except SyntaxError:
                    pass
                else:
                    executor = eval

            if executor is exec:
                try:
                    code = compile(cleaned, '<repl session>', 'exec')
                except SyntaxError as e:
                    await ctx.send(self.get_syntax_error(e))
                    continue

            variables['message'] = response

            fmt = None
            stdout = io.StringIO()

            try:
                with redirect_stdout(stdout):
                    result = executor(code, variables)
                    if inspect.isawaitable(result):
                        result = await result
            except Exception:
                value = stdout.getvalue()
                fmt = f'```py\n{value}{traceback.format_exc()}\n```'
            else:
                value = stdout.getvalue()
                if result is not None:
                    fmt = f'```py\n{value}{result}\n```'
                    variables['_'] = result
                elif value:
                    fmt = f'```py\n{value}\n```'

            try:
                if fmt is not None:
                    if len(fmt) > 2000:
                        await ctx.send('Content too big to be printed.')
                    else:
                        await ctx.send(fmt)
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await ctx.send(f'Unexpected error: `{e}`')

    @commands.command()
    async def geterror(self, ctx, error_number: int):
        """
        Gets an error from the internal error queue to diagnose issues quicker.
        """
        if error_number > self.bot.errors.maxlen:
            return await ctx.send('There are only 10 errors maximum in the queue!')
        if error_number > len(self.bot.errors):
            return await ctx.send("There aren't enough errors in the queue yet!")
        e = list(reversed(self.bot.errors))[error_number - 1]
        if isinstance(e, commands.errors.CommandInvokeError):
            return await ctx.send(''.join(traceback.format_exception(
                type(e), e.__cause__, e.__cause__.__traceback__)))
        else:
            return await ctx.send(''.join(traceback.format_exception(type(e), e, e.__traceback__)))

    @commands.command()
    async def load(self, ctx, *, module):
        """Loads a module."""
        _module = f'bot.cogs.{module}'
        try:
            self.bot.load_extension(_module)
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send(f'Loaded {_module}')

    @commands.command()
    async def unload(self, ctx, *, module):
        """Unloads a module."""
        _module = f'bot.cogs.{module}'
        try:
            self.bot.unload_extension(_module)
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send(f'Unloaded {_module}')

    @commands.group(invoke_without_command=True)
    async def reload(self, ctx, *, module):
        """Reloads a module."""
        _module = f'bot.cogs.{module}'
        try:
            self.bot.unload_extension(_module)
            self.bot.load_extension(_module)
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send(f'Reloaded {_module}')

    @reload.command(name='all')
    async def reload_all(self, ctx):
        """Reload all extensions."""
        ext = len(self.bot.extensions)
        counter = 0
        for extension in self.bot.extensions:
            try:
                self.bot.unload_extension(extension)
                self.bot.load_extension(extension)
                counter += 1
            except Exception as e:
                await ctx.send(f'Could not reload `{extension}` -> `{e}`')
            await asyncio.sleep(1)

        await ctx.send(f'Reloaded {counter}/{ext} extensions.')

    @commands.command(aliases=['dm'])
    async def reply(self, ctx, user: discord.User, *, reason: str):
        """DMs a user."""
        await user.send(reason)
        await ctx.send("The message has been sent!")

    @commands.command(aliases=['kill', 'die', 'endbot'])
    async def logout(self, ctx):
        """Kills the bot."""
        await ctx.send("Shutting down...")
        await ctx.bot.logout()

    @commands.group(aliases=['game'], invoke_without_command=True)
    async def activity(self, ctx, name: str, activity_type: str = "playing", url: str = None):
        """Sets the bots activity."""
        _activity_type = getattr(discord.ActivityType, activity_type)
        activity = discord.Activity(name=name, type=_activity_type, url=url)
        await self.bot.change_presence(activity=activity)
        await ctx.send(f"Changed Activity to `{activity_type.title()} {name}`!")

    @activity.command(name='off')
    async def activity_off(self, ctx):
        """Resets the bots status to default."""
        await self.bot.change_presence(activity=self.bot.activity)
        await ctx.send("Successfully reset bots activity!")


def setup(bot: Bot):
    """Setup function for the cog"""
    bot.add_cog(Owner(bot))
