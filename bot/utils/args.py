# coding=utf-8
"""ArgParse file for bot commands"""
import contextlib
import io
from argparse import Namespace, ArgumentParser as ArgP

from discord.ext.commands import Converter, BadArgument

command_parsers = {}


class Default(Namespace):
    """Default args for a command"""

    def __repr__(self):
        return f"'{' '.join(f'--{k}={v}'for k, v in self._get_kwargs())}'"


class Argument:
    """Class to hold arguments to be passed to add_argument"""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def register(self, parser):
        """Register an argument for a command"""
        parser.add_argument(*self.args, **self.kwargs)


class ArgumentParser(ArgP):
    """Custom parser class to redirect errors to the error handler"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, add_help=False, **kwargs)

    def error(self, exc):
        """Error raised for bad args"""
        raise BadArgument("An argument was incorrectly passed.")


def create_help(parser):
    """Creates an updated usage for the help command"""
    sio = io.StringIO()
    with contextlib.redirect_stdout(sio):
        parser.print_help()
    sio.seek(0)
    s = sio.read()
    # Strip the filename and trailing newline from help text
    return s[(len(str(s[7:]).split()[0]) + 8):-1]


class ArgParseConverter(Converter):
    """Custom command class for argparse"""

    def __init__(self, command_name, arguments, *args, **kwargs):
        self.arguments = arguments
        # Create the parser
        self.parser = ArgumentParser(*args, **kwargs)

        # Register all arguments
        for argument in arguments:
            argument.register(self.parser)
        self.do_help = True

        command_parsers[command_name] = self.parser

    async def convert(self, ctx, arg):
        """Convert passed arguments"""
        return self.parser.parse_args(arg.split())
