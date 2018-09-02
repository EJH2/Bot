# coding=utf-8
"""Overrides for Discord.py classes"""
import contextlib
import inspect
import io
import itertools

import discord
from discord.ext.commands import HelpFormatter as HelpF, Paginator, Command
from ghostbin import GhostBin

from bot.utils.args import ArgParseConverter as ArgPC


def create_help(cmd, parser):
    """Creates an updated usage for the help command"""
    default = cmd.params['args'].default
    if cmd.signature.split("[")[-1] == f"args={default}]" if default else "args]":
        sio = io.StringIO()
        with contextlib.redirect_stdout(sio):
            parser.print_help()
        sio.seek(0)
        s = sio.read()
        # Strip the filename and trailing newline from help text
        arg_part = s[(len(str(s[7:]).split()[0]) + 8):-1]
        k = cmd.qualified_name
        spt = len(k.split())
        # Remove a duplicate command name + leading arguments
        split_sig = cmd.signature.split()[spt:]
        return "[".join((" ".join(split_sig)).split("[")[:-1]) + arg_part
    return cmd.usage


class HelpFormatter(HelpF):
    """Custom override for the default help command"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def format(self):
        """Handles the actual behaviour involved with formatting.

        To change the behaviour, this method should be overridden.

        Returns
        --------
        list
            A paginated output of the help command.
        """
        self._paginator = Paginator()

        # we need a padding of ~80 or so

        description = self.command.description if not self.is_cog() else inspect.getdoc(self.command)

        if description:
            # <description> portion
            self._paginator.add_line(description, empty=True)

        if isinstance(self.command, Command):
            # <signature portion>
            if self.command.params.get("args", None) and type(self.command.params['args'].annotation) == ArgPC:
                self.command.usage = create_help(self.command, self.command.params['args'].annotation.parser)
            signature = self.get_command_signature()
            self._paginator.add_line(signature, empty=True)

            # <long doc> section
            if self.command.help:
                self._paginator.add_line(self.command.help, empty=True)

            # end it here if it's just a regular command
            if not self.has_subcommands():
                self._paginator.close_page()
                return self._paginator.pages

        max_width = self.max_name_size

        def category(tup):
            """Splits the help command into categories for easier readability"""
            cog = tup[1].cog_name
            # we insert the zero width space there to give it approximate
            # last place sorting position.
            return cog + ':' if cog is not None else '\u200bNo Category:'

        filtered = await self.filter_command_list()
        if self.is_bot():
            data = sorted(filtered, key=category)
            for category, commands in itertools.groupby(data, key=category):
                # there simply is no prettier way of doing this.
                commands = sorted(commands)
                if len(commands) > 0:
                    self._paginator.add_line(category)

                self._add_subcommands_to_page(max_width, commands)
        else:
            filtered = sorted(filtered)
            if filtered:
                self._paginator.add_line('Commands:')
                self._add_subcommands_to_page(max_width, filtered)

        # add the ending note
        self._paginator.add_line()
        ending_note = self.get_ending_note()
        self._paginator.add_line(ending_note)
        return self._paginator.pages


old_send = discord.abc.Messageable.send


async def send(self, content=None, **kwargs):
    """Overrides default send method in order to create a paste if the response is more than 2000 characters"""
    if content is not None and any(x in str(content) for x in ["@everyone", "@here"]):
        content = content.replace("@everyone", "@\u0435veryone").replace("@here", "@h\u0435re")
    if content is not None and len(str(content)) > 2000:
        paste = await GhostBin().paste(content, expire="15m")
        return await old_send(self, f"Hey, I couldn't handle all the text I was gonna send you, so I put it in a paste!"
                                    f"\nThe link is **{paste}**, but it expires in 15 minutes, so get it quick!",
                              **kwargs)
    else:
        return await old_send(self, content, **kwargs)
