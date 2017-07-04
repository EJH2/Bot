"""
Owner-only commands.
"""

import asyncio
import glob
import importlib
import inspect
import io
import json
import os
import subprocess
import sys
import textwrap
import traceback
from contextlib import redirect_stdout

import aiohttp
import discord
from discord.ext import commands

from discordbot import consts
from discordbot.bot import DiscordBot
from discordbot.cogs.utils import config
from discordbot.cogs.utils import util


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic
# noinspection PyBroadException,PyUnboundLocalVariable
# noinspection PyUnusedLocal,PyUnusedLocal,PyUnresolvedReferences,PyUnresolvedReferences,PyTypeChecker
class Owner:
    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()

    # ====================================================================
    #   Debugging related commands (Totally not ripped from Liara#0555 &
    #                             Danny#0007)
    # ====================================================================

    @staticmethod
    async def create_gist(content, filename='output.py'):
        github_file = {'files': {filename: {'content': str(content)}}}
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.github.com/gists', data=json.dumps(github_file)) as response:
                return await response.json()

    def cleanup_code(self, content):
        """
        Automatically removes code blocks from the code.
        """
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e):
        if e.text is None:
            return '```py\n{0.__class__.__name__}: {0}\n```'.format(e)
        return '```py\n{0.text}{1:>{0.offset}}\n{2}: {0}```'.format(e, '^', type(e).__name__)

    @commands.command()
    @commands.is_owner()
    async def debug(self, ctx, *, body: str):
        """
        Evaluate Python code.
        """
        env = {
            'bot': ctx.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'server': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = 'async def func():\n%s' % textwrap.indent(body, '  ')

        try:
            exec(to_compile, env)
        except SyntaxError as e:
            return await ctx.send(self.get_syntax_error(e))

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send('```py\n{}{}\n```'.format(value, traceback.format_exc()))
        else:
            value = stdout.getvalue()

            if ret is None:
                if value:
                    await ctx.send('```py\n%s\n```' % value)
            else:
                self._last_result = ret
                await ctx.send('```py\n%s%s\n```' % (value, ret))

    @commands.command()
    @commands.is_owner()
    async def repl(self, ctx):
        """
        Evaluate a bunch of Python code.
        """
        msg = ctx.message

        variables = {
            'ctx': ctx,
            'bot': ctx.bot,
            'message': ctx.message,
            'server': ctx.guild,
            'channel': ctx.channel,
            'author': ctx.author,
            '_': None,
        }

        if msg.channel.id in self.sessions:
            await ctx.send('Already running a REPL session in this channel. Exit it with `quit`.')
            return

        self.sessions.add(msg.channel.id)
        await ctx.send('Enter code to execute or evaluate. `exit()` or `quit` to exit.')

        def check(m):
            return m.author == msg.author and m.channel == msg.channel and m.content.startswith('`')
        while True:
            response = await self.bot.wait_for("message", check=check)

            cleaned = self.cleanup_code(response.content)

            if cleaned in ('quit', 'exit', 'exit()'):
                await ctx.send('Exiting.')
                self.sessions.remove(msg.channel.id)
                return

            executor = exec
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
            except Exception as e:
                value = stdout.getvalue()
                fmt = '```py\n{}{}\n```'.format(value, traceback.format_exc())
            else:
                value = stdout.getvalue()
                if result is not None:
                    fmt = '```py\n{}{}\n```'.format(value, result)
                    variables['_'] = result
                elif value:
                    fmt = '```py\n{}\n```'.format(value)

            try:
                if fmt is not None:
                    if len(fmt) > 2000:
                        gist = await self.create_gist(fmt.replace('``````', '```\n```'), filename='message.md')
                        await ctx.send('Sorry, that output was too large, so I uploaded it to gist instead.\n'
                                       '{0}'.format(gist['html_url']))
                    else:
                        await ctx.send(fmt)
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await ctx.send('Unexpected error: `{}`'.format(e))

    # ========================
    #   Bot related commands
    # ========================

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    async def appearance(self, ctx):
        """
        Command for getting/editing bot configs.
        """
        await ctx.send("Invalid subcommand passed: {0.subcommand_passed}".format(ctx), delete_after=5)

    @appearance.command(name="game")
    @commands.is_owner()
    async def appearance_game(self, ctx, game: str, *, url: str = None):
        """
        Change the bots game.
        """
        if not url:
            status = discord.Game(name=game, type=0)
        else:
            status = discord.Game(name=game, url=url, type=1)

        await ctx.bot.change_presence(game=status)
        await ctx.send("Changed game to {}{}.".format(game, " on " + url if url else ""))

    @appearance.command(name="status")
    @commands.is_owner()
    async def appearance_status(self, ctx, *, status: str):
        """
        Change the bots online status.
        """
        await ctx.change_presence(status=discord.Status(status))

    @appearance.command(name="name")
    @commands.is_owner()
    async def appearance_name(self, ctx, *, name: str):
        """
        Change the bot name.
        """
        await ctx.bot.user.edit(username=name)
        await ctx.send("Changed name to {}.".format(name))

    @appearance.command(name="avatar")
    @commands.is_owner()
    async def appearance_avatar(self, ctx, *, url: str):
        """
        Change the bot's avatar.
        """
        avatar = await util.get_file(url)
        await ctx.bot.user.edit(avatar=avatar)
        await ctx.send("Changed avatar.")

    # ===========================
    #   Module related commands
    # ===========================

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, *, extension: str):
        """
        Load an extension.
        """
        extension = extension.lower()
        extent = "discordbot.cogs.{}".format(extension) in self.bot.extensions
        if extent:
            return await ctx.send("Could not load `{}` -> `It's already loaded!`".format(extension))
        try:
            ext = ctx.bot.load_extension("discordbot.cogs.{}".format(extension))
            await ctx.send("Loaded cog `discordbot.cogs.{}`.".format(extension))
        except Exception as e:
            traceback.print_exc()
            await ctx.send("Could not load `{}` -> `{}`".format(extension, e))

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, *, extension: str):
        """
        Unload an extension.
        """
        extension = extension.lower()
        ext = "discordbot.cogs.{}".format(extension) in self.bot.extensions
        ctx.bot.unload_extension("discordbot.cogs.{}".format(extension))
        if ext is False:
            await ctx.send("Could not unload `{}` -> `Either it doesn't exist or it's already unloaded!`".format(
                extension))
        else:
            await ctx.send("Unloaded `{}`.".format(extension))

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, *, extension: str):
        """
        Reload an extension.
        """
        extension = extension.lower()
        try:
            ctx.bot.unload_extension("discordbot.cogs.{}".format(extension))
            ctx.bot.load_extension("discordbot.cogs.{}".format(extension))
        except Exception as e:
            traceback.print_exc()
            await ctx.send("Could not reload `{}` -> `{}`".format(extension, e))
        else:
            await ctx.send("Reloaded `{}`.".format(extension))

    @commands.command()
    @commands.is_owner()
    async def reloadall(self, ctx):
        """
        Reload all extensions.
        """
        for extension in ctx.bot.extensions:
            try:
                ctx.bot.unload_extension(extension)
                ctx.bot.load_extension(extension)
                await asyncio.sleep(1)
            except Exception as e:
                await ctx.send("Could not reload `{}` -> `{}`".format(extension, e))
                await asyncio.sleep(1)

        await ctx.send("Reloaded all.")

    @commands.command()
    @commands.is_owner()
    async def refresh(self, ctx):
        """
        Re-initialise the cogs folder.
        """
        await ctx.send("Please wait...")

        for extension in consts.modules:
            ctx.bot.unload_extension("discordbot.cogs.{}".format(extension))
            await ctx.send("Unloaded `{}`.".format(extension))

        consts.modules = []

        for i in glob.glob(os.getcwd() + "/discordbot/cogs/*.py"):
            if "init" not in i:
                modules.append(i.replace(os.getcwd() + "/", "").replace("\\", ".").replace("/", ".")[:-3])

        for extension in consts.modules:
            try:
                ctx.load_extension(extension)
            except Exception as e:
                ctx.send("Could not load module `{}` -> `{}`".format(extension, e))
                await asyncio.sleep(1)
            else:
                ctx.bot.logger.info("Loaded extension `{}`.".format(extension))
                await asyncio.sleep(1)

        await ctx.send("Refreshed all modules!")

    # ===============================
    #   Management related commands
    # ===============================

    @commands.command()
    @commands.is_owner()
    async def dm(self, ctx, user_id: int, *, reason: str):
        user = ctx.bot.get_user(id)
        if user is not None:
            await user.send(reason)
            await ctx.send("The message has been sent!")
        else:
            await ctx.send("I couldn't find that user, sorry!")

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    async def settings(self, ctx):
        """
        Command for getting/editing bot configs.
        """
        await ctx.send("Invalid subcommand passed: {0.subcommand_passed}".format(ctx), delete_after=5)

    @settings.command()
    async def get(self, ctx, configfile, *, keys: str):
        """
        Gets a config value.
        """
        keys = keys.split(", ")
        configfile = config.Config(configfile).to_dict()
        value = configfile
        for x in keys:
            value = dict.get(value, x)
        if value is not None:
            await ctx.send(value)
            return
        else:
            await ctx.send("I couldn't find that key in the specified config!")

    @settings.command()
    async def set(self, ctx, configfile, keys, *, value):
        """
        Sets a config value.
        """
        configfile = config.Config(configfile)
        config_file = configfile.db
        keys = keys.split(", ")
        if len(keys) > 1:
            for x in keys[:-1]:
                config_file = dict.get(config_file, x)
        end = "".join(keys[-1:])
        start = "".join(keys[:-1])
        config_file[end] = value
        configfile.db[start] = config_file
        configfile.save()
        if hasattr(ctx.bot, end):
            if keys == "command_prefix":
                ctx.bot.command_prefix = commands.when_mentioned_or(value)
            else:
                setattr(ctx.bot, end, value)
        importlib.reload(consts)
        await ctx.send("Alright, I changed `{}` to `{}`!".format(end, value))

    @commands.command()
    @commands.is_owner()
    async def endbot(self, ctx):
        """
        Segfault the bot in order to kill it.
        """
        await ctx.send("Goodbye!")
        self.bot.restarting.delete("restarting")
        await ctx.bot.logout()
        return

    @commands.command()
    @commands.is_owner()
    async def restart(self, ctx):
        """
        Restart the bot.
        """
        await ctx.send("Restarting...")
        self.bot.restarting.place("restarting", "True")
        self.bot.restarting.place("restart_channel", ctx.message.channel.id)
        ctx.bot.logger.info("\n"
                            "-------------------"
                            "\n")
        await ctx.bot.logout()
        subprocess.call([sys.executable, ctx.bot.filename])

    @commands.command()
    @commands.is_owner()
    async def botban(self, ctx, *, member: discord.Member):
        """
        Bans a user from using the bot.
        """
        if member.id == ctx.bot.owner_id:
            await ctx.send("You can't bot ban the owner!")
            return

        plonks = self.bot.ignored.get("users", [])
        if member.id in plonks:
            await ctx.send("That user is already bot banned.")
            return

        plonks.append(member.id)
        self.bot.ignored.place("users", plonks)
        await ctx.send("{0.name} has been banned from using the bot.".format(member))

    @commands.command()
    @commands.is_owner()
    async def unbotban(self, ctx, *, member: discord.Member):
        """
        Unbans a user from using the bot.
        """
        if member.id == ctx.bot.owner_id:
            await ctx.send("You can't un-bot ban the owner, because he can't be banned!")
            return

        plonks = self.bot.ignored.get("users", [])
        if member.id not in plonks:
            await ctx.send("That user isn't bot banned.")
            return

        self.bot.ignored.remove("users", member.id)
        await ctx.send("{0.name} has been unbanned from using the bot.".format(member))

    @commands.command()
    @commands.is_owner()
    async def sneaky(self, ctx, *, server: str):
        """
        Generates an invite link for the specified server.
        """
        invite = await ctx.bot.create_invite(destination=discord.utils.find(lambda m: m.name == server, ctx.bot.guilds))
        await ctx.send(invite)


def setup(bot: DiscordBot):
    bot.add_cog(Owner(bot))
