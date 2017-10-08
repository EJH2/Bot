"""
Owner-only commands for the bot.
"""
import asyncio
import glob
import inspect
import io
import os
import textwrap
import traceback
from contextlib import redirect_stdout

import discord
from discord.ext import commands

from discordbot.main import DiscordBot
from discordbot.utils import util, tables


class Owner:
    """
    Owner-only commands for the bot.
    """

    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.db = bot.db
        self._last_result = None
        self.sessions = set()

    # ===================================================================
    #   Debugging related commands (Totally not ripped from Danny#0007)
    # ===================================================================

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
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @commands.is_owner()
    @commands.command()
    async def debug(self, ctx, *, body: str):
        """Evaluates code."""

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
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()

            if ret is None:
                if value and len(str(value)) < 1980:
                    await ctx.send(f'```py\n{value}\n```')
                else:
                    print(f'{value}, {len(value), value.__class__}')
                    # paste = await self.bot.get_cog("GhostBin").paste_logs(value, "15m")
                    # return await ctx.send(
                    #     f'**Your requested sauce was too stronk. So I uploaded to GhostBin! Hurry, it expires'
                    #     f' in 15 minutes!**\n<{paste}>')
            else:
                self._last_result = ret
                if len(str(value)) + len(str(ret)) < 1980:
                    await ctx.send(f'```py\n{value}{ret}\n```')
                else:
                    paste = await self.bot.get_cog("GhostBin").paste_logs(f'{value}{ret}', "15m")
                    return await ctx.send(
                        f'**Your requested sauce was too stronk. So I uploaded to GhostBin! Hurry, it expires'
                        f' in 15 minutes!**\n<{paste}>')

    @commands.is_owner()
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
            return m.author.id == ctx.author.id and \
                   m.channel.id == ctx.channel.id and \
                   m.content.startswith('`')

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
                        paste = await self.bot.get_cog("GhostBin").paste_logs(fmt[6:-4], "15m")
                        await ctx.send(
                            f'**Your requested sauce was too stronk. So I uploaded to GhostBin! Hurry, it expires'
                            f' in 15 minutes!**\n<{paste}>')
                    else:
                        await ctx.send(fmt)
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await ctx.send(f'Unexpected error: `{e}`')

    # ========================
    #   Bot related commands
    # ========================

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    async def appearance(self, ctx):
        """Command for changing the bot's appearance."""
        raise commands.BadArgument(f"Invalid subcommand passed: {ctx.subcommand_passed}")

    @appearance.command(name="game")
    @commands.is_owner()
    async def appearance_game(self, ctx, game: str, *, url: str = None):
        """Change the bots game."""
        if not url:
            status = discord.Game(name=game, type=0)
        else:
            status = discord.Game(name=game, url=url, type=1)

        await self.bot.change_presence(game=status)
        await ctx.send(f"Changed game to {game}{' on ' + url if url else ''}.")

    @appearance.command(name="status")
    @commands.is_owner()
    async def appearance_status(self, ctx, *, status: str):
        """Change the bots online status."""
        await self.bot.change_presence(status=discord.Status(status))
        await ctx.send(f"I am now {status}!")

    @appearance.command(name="name")
    @commands.is_owner()
    async def appearance_name(self, ctx, *, name: str):
        """Change the bot name."""
        await self.bot.user.edit(username=name)
        await ctx.send(f"Changed name to {name}.")

    @appearance.command(name="avatar")
    @commands.is_owner()
    async def appearance_avatar(self, ctx, *, url: str):
        """Change the bot's avatar."""
        avatar = await util.get_file(self.bot, url)
        await self.bot.user.edit(avatar=avatar)
        await ctx.send("Changed avatar.")

    # ===========================
    #   Module related commands
    # ===========================

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, *, extension: str):
        """Load an extension."""
        extension = extension.lower()
        extent = f"discordbot.cogs.{extension}" in self.bot.extensions
        if extent:
            return await ctx.send(f"Could not load `{extension}` -> `It's already loaded!`")
        try:
            self.bot.load_extension(f"discordbot.cogs.{extension}")
            await ctx.send(f"Loaded cog `discordbot.cogs.{extension}`.")
        except Exception as e:
            traceback.print_exc()
            await ctx.send(f"Could not load `{extension}` -> `{e}`")

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, *, extension: str):
        """Unload an extension."""
        extension = extension.lower()
        ext = f"discordbot.cogs.{extension}" in self.bot.extensions
        self.bot.unload_extension(f"discordbot.cogs.{extension}")
        if ext is False:
            await ctx.send(f"Could not unload `{extension}` -> `Either it doesn't exist or it's already unloaded!`")
        else:
            await ctx.send(f"Unloaded `{extension}`.")

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    async def reload(self, ctx, *, extension: str):
        """Reload an extension."""
        extension = extension.lower()
        try:
            self.bot.unload_extension(f"discordbot.cogs.{extension}")
            self.bot.load_extension(f"discordbot.cogs.{extension}")
        except Exception as e:
            traceback.print_exc()
            await ctx.send(f"Could not reload `{extension}` -> `{e}`")
        else:
            await ctx.send(f"Reloaded `{extension}`.")

    @reload.command()
    @commands.is_owner()
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
                await ctx.send(f"Could not reload `{extension}` -> `{e}`")
            await asyncio.sleep(1)

        await ctx.send(f"Reloaded {counter}/{ext} extensions.")

    @commands.command()
    @commands.is_owner()
    async def refresh(self, ctx):
        """Re-initialise the cogs folder."""
        await ctx.send("Please wait...")

        modules = len(self.bot.modules)
        counter = 0
        for extension in self.bot.modules:
            try:
                self.bot.unload_extension(f"discordbot.cogs.{extension}")
                counter += 1
            except Exception as e:
                await ctx.send(f"Could not load module `{extension}` -> `{e}`")
        await ctx.send(f"{counter}/{modules} unloaded!")

        self.bot.modules = []

        for i in glob.glob(os.getcwd() + "/discordbot/cogs/*.py"):
            if "init" not in i:
                self.bot.modules.append(i.replace(os.getcwd() + "/", "").replace("\\", ".").replace("/", ".")[:-3])

        counter = 0
        for extension in self.bot.modules:
            try:
                self.bot.load_extension(extension)
                counter += 1
            except Exception as e:
                await ctx.send(f"Could not load module `{extension}` -> `{e}`")
            await asyncio.sleep(1)
        await ctx.send(f"{counter}/{modules} loaded!")

    # ===============================
    #   Management related commands
    # ===============================

    @commands.command()
    @commands.is_owner()
    async def dm(self, ctx, user: discord.User, *, reason: str):
        """DMs a user."""
        if user is not None:
            await user.send(reason)
            await ctx.send("The message has been sent!")
        else:
            await ctx.send("I couldn't find that user, sorry!")

    @commands.command()
    @commands.is_owner()
    async def endbot(self, ctx):
        """Log out the bot."""
        await ctx.send("Goodbye!")
        await self.bot.logout()

    @commands.command()
    @commands.is_owner()
    async def botban(self, ctx, member: discord.User, *, reason: str = "Excessive Stupid"):
        """Bans a user from using the bot."""
        if not self.db:
            return await ctx.send("Database is down, try again later?")
        if member.id == self.bot.owner_id:
            return await ctx.send("You can't bot ban the owner!")

        plonks = self.bot.ignored.get("users", [])
        if member.id in plonks:
            return await ctx.send("That user is already bot banned.")

        plonks.append(member.id)
        values = {"object_id": member.id, "type": "user", "reason": reason}
        async with self.db.get_session() as s:
            await s.add(tables.Ignored(**values))
        self.bot.ignored["users"] = plonks
        await ctx.send(f"{member.name} has been banned from using the bot for `{reason}`.")

    @commands.command()
    @commands.is_owner()
    async def unbotban(self, ctx, *, member: discord.User):
        """Unbans a user from using the bot."""
        if not self.db:
            return await ctx.send("Database is down, try again later?")
        if member.id == self.bot.owner_id:
            return await ctx.send("You can't un-bot ban the owner, because they can't be banned!")

        plonks = self.bot.ignored.get("users", [])
        if member.id not in plonks:
            return await ctx.send("That user isn't bot banned.")

        plonks.remove(member.id)
        async with self.db.get_session() as s:
            entry = await s.select(tables.Ignored).where(tables.Ignored.object_id == member.id).first()
            await s.remove(entry)
        self.bot.ignored["users"] = plonks
        await ctx.send(f"{member.name} has been unbanned from using the bot.")

    @commands.command()
    @commands.is_owner()
    async def sneaky(self, ctx, *, server: str):
        """Generates an invite link for the specified server."""
        server = discord.utils.get(self.bot.guilds, name=server)
        channels = [c for c in server.channels if c.permissions_for(server.me).create_instant_invite]
        if len(channels) > 0:
            invite = await channels[0].create_invite(max_uses=1)
            return await ctx.send(invite)
        await ctx.send("I can't invite from any channels. Sorry!")


def setup(bot: DiscordBot):
    bot.add_cog(Owner(bot))
