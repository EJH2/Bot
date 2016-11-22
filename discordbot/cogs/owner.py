"""
Owner-only commands.
"""

import glob
import inspect
import io
import os
import subprocess
import sys
import traceback
from contextlib import redirect_stdout

import discord
from discord.ext import commands

from discordbot import consts
from discordbot.bot import DiscordBot
from discordbot.cogs.utils import config
from discordbot.cogs.utils import util
from discordbot.cogs.utils.checks import is_owner


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic
# noinspection PyBroadException,PyUnboundLocalVariable
# noinspection PyUnusedLocal,PyUnusedLocal,PyUnresolvedReferences,PyUnresolvedReferences,PyTypeChecker
class Owner:
    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.config = config.Config("ignored.yaml")
        self.restarting = config.Config("restart.yaml")
        self.sessions = set()

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

        # remove `foo`
        return content.strip("` \n")

    def get_syntax_error(self, e):
        return "```py\n{0.text}{1:>{0.offset}}\n{2}: {0}```".format(e, "^", type(e).__name__)

    @commands.command()
    @commands.check(is_owner)
    async def game(self, game: str, *, url: str = None):
        """
        Change the bots game.
        """
        if not url:
            game = discord.Game(name=game, type=0)
        else:
            game = discord.Game(name=game, url=url, type=1)

        await self.bot.change_presence(game=game)

    @commands.command()
    @commands.check(is_owner)
    async def status(self, *, status: str):
        """
        Change the bots online status.
        """
        await self.bot.change_presence(status=discord.Status(status))

    @commands.command()
    @commands.check(is_owner)
    async def name(self, *, name: str):
        """
        Change the bot name.
        """
        await self.bot.edit_profile(username=name)
        await self.bot.say("Changed name to {}.".format(name))

    @commands.command()
    @commands.check(is_owner)
    async def setavatar(self, *, url: str):
        """
        Change the bot's avatar.
        """
        avatar = await util.get_file(url)
        await self.bot.edit_profile(avatar=avatar)
        await self.bot.say("Changed avatar.")

    @commands.command(pass_context=True)
    async def banmenigger(self, ctx):
        try:
            await self.bot.ban(ctx.message.author)
            await self.bot.say(":ok_hand:")
        except:
            await self.bot.say(":not_ok_hand:")

    @commands.command()
    @commands.check(is_owner)
    async def load(self, *, extension: str):
        """
        Load an extension.
        """
        extension = extension.lower()
        try:
            self.bot.load_extension("discordbot.cogs.{}".format(extension))
        except Exception as e:
            traceback.print_exc()
            await self.bot.say("Could not load `{}` -> `{}`".format(extension, e))
        else:
            await self.bot.say("Loaded cog `discordbot.cogs.{}`.".format(extension))

    @commands.command()
    @commands.check(is_owner)
    async def unload(self, *, extension: str):
        """
        Unload an extension.
        """
        extension = extension.lower()
        try:
            self.bot.unload_extension("dicordbot.cogs.{}".format(extension))
        except Exception as e:
            traceback.print_exc()
            await self.bot.say("Could not unload `{}` -> `{}`".format(extension, e))
        else:
            await self.bot.say("Unloaded `{}`.".format(extension))

    @commands.command()
    @commands.check(is_owner)
    async def reload(self, *, extension: str):
        """
        Reload an extension.
        """
        extension = extension.lower()
        try:
            self.bot.unload_extension("discordbot.cogs.{}".format(extension))
            self.bot.load_extension("discordbot.cogs.{}".format(extension))
        except Exception as e:
            traceback.print_exc()
            await self.bot.say("Could not reload `{}` -> `{}`".format(extension, e))
        else:
            await self.bot.say("Reloaded `{}`.".format(extension))

    @commands.command()
    @commands.check(is_owner)
    async def reloadall(self):
        """
        Reload all extensions.
        """
        for extension in self.bot.extensions:
            try:
                self.bot.unload_extension(extension)
                self.bot.load_extension(extension)
            except Exception as e:
                await self.bot.say("Could not reload `{}` -> `{}`".format(extension, e))

        await self.bot.say("Reloaded all.")

    @commands.command()
    @commands.check(is_owner)
    async def refresh(self):
        """
        Re-initialise the cogs folder.
        """
        await self.bot.say("Please wait...")

        for extension in consts.modules:
            try:
                self.bot.unload_extension(extension)
            except Exception as e:
                await self.bot.say("Could not unload `{}` -> `{}`".format(extension, e))

        consts.modules = []

        for i in glob.glob(os.getcwd() + "/discordbot/cogs/*.py"):
            consts.modules.append(i.replace(os.getcwd() + "/", "").replace("\\", ".").replace("/", ".")[:-3])

        for extension in consts.modules:
            try:
                self.bot.load_extension(extension)
            except Exception as e:
                self.bot.logger.critical("Could not load module {}, {}".format(extension, e))
            else:
                self.bot.logger.info("Loaded extension {}.".format(extension))

        await self.bot.say("Refreshed all modules!")

    @commands.command()
    @commands.check(is_owner)
    async def endbot(self):
        """
        Segfault the bot in order to kill it.
        """
        await self.bot.say("Goodbye!")
        self.restarting.delete("restarting")
        await self.bot.logout()
        return

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def restart(self, ctx):
        """
        Restart the bot.
        """
        await self.bot.say("Restarting...")
        self.restarting.place("restarting", "True")
        self.restarting.place("restart_channel", ctx.message.channel.id)
        child = subprocess.Popen("python bot.py", shell=True, stdout=subprocess.PIPE)
        output, error = child.communicate()
        print(output, error)
        sys.exit()

    @commands.command(pass_context=True, hidden=True)
    @commands.check(is_owner)
    async def debug(self, ctx, *, code: str):
        """Evaluates code."""
        code = code.strip("` ")
        python = "```py\n{}\n```"
        result = None

        env = {
            "bot": self.bot,
            "ctx": ctx,
            "message": ctx.message,
            "server": ctx.message.server,
            "channel": ctx.message.channel,
            "author": ctx.message.author
        }

        env.update(globals())

        try:
            result = eval(code, env)
            if inspect.isawaitable(result):
                await result
                return
        except Exception as e:
            await self.bot.say(python.format(type(e).__name__ + ": " + str(e)))
            traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
            return

        await self.bot.say(python.format(result))

    @commands.command(pass_context=True, hidden=True)
    @commands.check(is_owner)
    async def repl(self, ctx):
        msg = ctx.message

        variables = {
            "ctx": ctx,
            "bot": self.bot,
            "message": msg,
            "server": msg.server,
            "channel": msg.channel,
            "author": msg.author,
            "last": None,
        }

        if msg.channel.id in self.sessions:
            await self.bot.say("Already running a REPL session in this channel. Exit it with `quit`.")
            return

        self.sessions.add(msg.channel.id)
        await self.bot.say("Enter code to execute or evaluate. `exit()` or `quit` to exit.")
        while True:
            response = await self.bot.wait_for_message(author=msg.author, channel=msg.channel,
                                                       check=lambda m: m.content.startswith("`"))

            cleaned = self.cleanup_code(response.content)

            if cleaned in ("quit", "exit", "exit()"):
                await self.bot.say("Exiting.")
                self.sessions.remove(msg.channel.id)
                return

            executor = exec
            if cleaned.count("\n") == 0:
                # single statement, potentially "eval"
                try:
                    code = compile(cleaned, "<repl session>", "eval")
                except SyntaxError:
                    pass
                else:
                    executor = eval

            if executor is exec:
                try:
                    code = compile(cleaned, "<repl session>", "exec")
                except SyntaxError as e:
                    await self.bot.say(self.get_syntax_error(e))
                    continue

            variables["message"] = response

            fmt = None
            stdout = io.StringIO()

            try:
                with redirect_stdout(stdout):
                    result = executor(code, variables)
                    if inspect.isawaitable(result):
                        result = await result
            except Exception as e:
                value = stdout.getvalue()
                fmt = "```py\n{}{}\n```".format(value, traceback.format_exc())
            else:
                value = stdout.getvalue()
                if result is not None:
                    fmt = "```py\n{}{}\n```".format(value, result)
                    variables["last"] = result
                elif value:
                    fmt = "```py\n{}\n```".format(value)

            try:
                if fmt is not None:
                    if len(fmt) > 2000:
                        await self.bot.send_message(msg.channel, "Content too big to be printed.")
                    else:
                        await self.bot.send_message(msg.channel, fmt)
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await self.bot.send_message(msg.channel, "Unexpected error: `{}`".format(e))

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def botban(self, ctx, *, member: discord.Member):
        """
        Bans a user from using the bot.
        """
        if member.id == ctx.bot.owner_id:
            await self.bot.say("You can0't bot ban the owner!")
            return

        plonks = self.config.get("users", [])
        if member.id in plonks:
            await self.bot.say("That user is already bot banned.")
            return

        plonks.append(member.id)
        self.config.place("users", plonks)
        await self.bot.say("{0.name} has been banned from using the bot.".format(member))

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def unbotban(self, ctx, *, member: discord.Member):
        """
        Unbans a user from using the bot.
        """
        if member.id == ctx.bot.owner_id:
            await self.bot.say("You can't un-bot ban the owner, because he can't be banned!")
            return

        plonks = self.config.get("users", [])
        if member.id not in plonks:
            await self.bot.say("That user isn't bot banned.")
            return

        self.config.remove("users", member.id)
        await self.bot.say("{0.name} has been unbanned from using the bot.".format(member))

    @commands.command()
    @commands.check(is_owner)
    async def sneaky(self, *, server: str):
        """
        Generates an invite link for the specified server.
        """
        invite = await self.bot.create_invite(discord.utils.find(lambda m: m.name == server, self.bot.servers))
        await self.bot.say(str(invite))


def setup(bot: DiscordBot):
    bot.add_cog(Owner(bot))
