"""
Owner-only commands.
"""

import asyncio
import glob
import importlib
import os
import subprocess
import sys
import traceback
import textwrap
import time

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
        self.ignored = config.Config("ignored.yaml")
        self.restarting = config.Config("restart.yaml")
        self.sessions = set()
        self._eval = {'env': {}, 'count': 0}

    # =====================================================================
    #   Debugging related commands (Totally not ripped from Liara#0555 at
    #   https://github.com/Thessia/Liara/blob/rewrite/cogs/core.py#L370)
    # =====================================================================

    @staticmethod
    async def create_gist(content, filename='output.py'):
        github_file = {'files': {filename: {'content': str(content)}}}
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.github.com/gists', data=json.dumps(github_file)) as response:
                return await response.json()

    @commands.command()
    @commands.is_owner()
    async def debug(self, ctx, *, code: str):
        """Evaluates Python code."""

        self._eval['env'].update({
            'bot': self.bot,
            'ctx': ctx,
            'message': ctx.message,
            'channel': ctx.message.channel,
            'guild': ctx.message.guild,
            'author': ctx.message.author,
        })

        # let's make this safe to work with
        code = code.replace('```py\n', '').replace('```', '').replace('`', '')

        _code = 'async def func(self):\n  try:\n{}\n  finally:\n    self._eval[\'env\'].update(locals())' \
            .format(textwrap.indent(code, '    '))

        before = time.monotonic()
        # noinspection PyBroadException
        try:
            exec(_code, self._eval['env'])

            func = self._eval['env']['func']
            output = await func(self)

            if output is not None:
                output = repr(output)
        except Exception as e:
            output = ""
            out = traceback.format_exception(type(e), e, e.__traceback__)
            for i in out:
                output += i
        after = time.monotonic()

        self._eval['count'] += 1
        count = self._eval['count']
        message = None

        if output is not None:
            message = '```diff\n+ In [{}]:\n``````py\n{}\n```'.format(count, code)
            message += '\n```diff\n- Out[{}]:\n``````py\n{}\n```'.format(count, output)
            message += '\n*{}ms*'.format(round((after - before) * 1000))

        if message is not None:
            try:
                if ctx.author.id == self.bot.user.id:
                    await ctx.message.edit(content=message)
                else:
                    await ctx.send(message)
            except discord.HTTPException:
                await ctx.trigger_typing()
                gist = await self.create_gist(message.replace('``````', '```\n```'), filename='message.md')
                await ctx.send('Sorry, that output was too large, so I uploaded it to gist instead.\n'
                               '{0}'.format(gist['html_url']))

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
        try:
            ext = ctx.bot.load_extension("discordbot.cogs.{}".format(extension))
        except Exception as e:
            traceback.print_exc()
            await ctx.send("Could not load `{}` -> `{}`".format(extension, e))
        else:
            if ext is not None:
                await ctx.send("Loaded cog `discordbot.cogs.{}`.".format(extension))
            else:
                await ctx.send("Could not load `{}` -> `It's already loaded!`".format(extension))

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, *, extension: str):
        """
        Unload an extension.
        """
        extension = extension.lower()
        ext = ctx.bot.unload_extension("discordbot.cogs.{}".format(extension))
        if ext is None:
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
            ext = ctx.bot.unload_extension("discordbot.cogs.{}".format(extension))
            if ext is None:
                await ctx.send("Could not unload `{}` -> It doesn't exist!".format(extension))
            else:
                await ctx.send("Unloaded `{}`.".format(extension))

        consts.modules = []

        for i in glob.glob(os.getcwd() + "/discordbot/cogs/*.py"):
            consts.modules.append(i.replace(os.getcwd() + "/", "").replace("\\", ".").replace("/", ".")[:-3])

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
        if len(keys) > 1:
            keys = keys.split(", ")
            configfile = config.Config(configfile)
            configfile_dict = configfile.to_dict()
            key = configfile_dict
            for x in keys[:-1]:
                key = dict.get(key, x)
            keys = "".join(keys[-1:])
            key[keys] = value
            configfile.save()
            if hasattr(ctx.bot, keys):
                ctx.bot.__dict__[keys] = value
            importlib.reload(consts)
        else:
            configfile = config.Config(configfile)
            configfile_dict = configfile.to_dict()
            key = configfile_dict
            keys = "".join(keys[-1:])
            key[keys] = value
            configfile.save()
            if hasattr(ctx.bot, keys):
                ctx.bot.__dict__[keys] = value
            importlib.reload(consts)

    @commands.command()
    @commands.is_owner()
    async def endbot(self, ctx):
        """
        Segfault the bot in order to kill it.
        """
        await ctx.send("Goodbye!")
        self.restarting.delete("restarting")
        await ctx.bot.logout()
        return

    @commands.command()
    @commands.is_owner()
    async def restart(self, ctx):
        """
        Restart the bot.
        """
        await ctx.send("Restarting...")
        self.restarting.place("restarting", "True")
        self.restarting.place("restart_channel", ctx.message.channel.id)
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

        plonks = self.ignored.get("users", [])
        if member.id in plonks:
            await ctx.send("That user is already bot banned.")
            return

        plonks.append(member.id)
        self.ignored.place("users", plonks)
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

        plonks = self.ignored.get("users", [])
        if member.id not in plonks:
            await ctx.send("That user isn't bot banned.")
            return

        self.ignored.remove("users", member.id)
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
