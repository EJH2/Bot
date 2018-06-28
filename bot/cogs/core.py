# coding=utf-8
"""File containing core commands of the bot"""
import asyncio
import datetime
import inspect
import io
import os
import textwrap
import time
import traceback
from contextlib import redirect_stdout
from pathlib import Path

import discord
import git
import humanize
from discord.ext import commands

from bot.main import Bot


class Core:
    """Cog containing core commands of the bot"""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()
        self.revision_loop = self.bot.loop.create_task(self.get_revisions())

    async def get_revisions(self):
        """_get_revisions but for a looped task"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self._get_revisions()
            await asyncio.sleep(3600)

    async def _get_revisions(self):
        """Get latest git revisions"""
        repo = git.Repo(os.getcwd())
        url = repo.remote().urls.__next__()
        commit_url = url.split("@")[1].replace(":", "/")[:-4]
        commits = []
        unpublished_commits = list(repo.iter_commits('master@{u}..master'))
        for commit in list(repo.iter_commits("master"))[:3]:
            commit_time = humanize.naturaltime(datetime.datetime.now(tz=commit.committed_datetime.tzinfo)
                                               - commit.committed_datetime)
            if commit not in unpublished_commits:
                commits.append(f"[`{commit.hexsha[:7]}`](https://{commit_url}/commit/{commit.hexsha[:7]}) "
                               f"{commit.summary} ({commit_time})")
            else:
                commits.append(f"`{commit.hexsha[:7]}` {commit.summary} ({commit_time})")
        self.bot.revisions = '\n'.join(commits)

    @staticmethod
    def cleanup_code(content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @staticmethod
    def get_syntax_error(e):
        """Parses errors into a codeblock for easy reading"""
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @commands.command(hidden=True)
    async def load(self, ctx, *, module):
        """Loads a module."""
        _module = f'bot.cogs.{module}'
        try:
            self.bot.load_extension(_module)
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send(f'Loaded {_module}')

    @commands.command(hidden=True)
    async def unload(self, ctx, *, module):
        """Unloads a module."""
        _module = f'bot.cogs.{module}'
        try:
            self.bot.unload_extension(_module)
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send(f'Unloaded {_module}')

    @commands.command(hidden=True)
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

    @commands.command(hidden=True, aliases=['kill', 'die', 'endbot'])
    async def logout(self, ctx):
        """Kills the bot"""
        await ctx.send("Shutting down...")
        await ctx.bot.logout()

    # @commands.command(hidden=True)
    # async def activity(self, ctx, ):
    # TODO: Actually finish this sometime, or not ¯\_(ツ)_/¯

    @commands.command(hidden=True)
    async def debug(self, ctx, *, body: str):
        """Evaluates a code"""

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

    @commands.command(hidden=True)
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


def setup(bot: Bot):
    """Setup function for the cog"""
    bot.add_cog(Core(bot))
