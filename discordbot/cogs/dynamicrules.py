"""
Dynamic Rules for the bot.
"""
import asyncio
import json

import asyncqlio
from discord.ext import commands

from discordbot.main import DiscordBot
from discordbot.utils import checks, util, exceptions, tables


async def needs_setup(ctx):
    server = ctx.guild
    async with ctx.bot.db.get_session() as s:
        query = await s.select(tables.Dynamic_Rules).where(tables.Dynamic_Rules.guild_id == server.id).all()
        query = await query.flatten()
    if len(query) == 0:
        msg = f"You don't have Dynamic Rules set up! Use {ctx.bot.command_prefix_}dynamicrules setup"
        raise exceptions.ClearanceError(msg)
    return True


class DynamicRules:
    """
    Dynamic Rules for the bot.
    """

    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.db = bot.db

        self.valid_settings = {"command_prefix": str}

    # ============================
    #    Dynamic Rules Commands
    # ============================

    @commands.group(invoke_without_command=True, aliases=["dynrules"])
    async def dynamicrules(self, ctx):
        """Base command for Dynamic Rules!"""
        raise commands.BadArgument(f"Invalid subcommand passed: {ctx.subcommand_passed}")

    @dynamicrules.command(name="setup")
    @commands.check(checks.permissions(manage_messages=True))
    async def dynamicrules_setup(self, ctx):
        """Sets up the server to use Dynamic Rules. This is to de-clutter the DB."""
        server = ctx.guild
        async with self.bot.db.get_session() as s:
            query = await s.select(tables.Dynamic_Rules).where(tables.Dynamic_Rules.guild_id == server.id).all()
            query = await query.flatten()
        if len(query) == 0:
            try:
                async with self.bot.db.get_session() as s:
                    await s.add(tables.Dynamic_Rules(guild_id=server.id, attrs="{}"))
                await ctx.send("Dynamic Rules entry successfully created for this server!")
            except asyncqlio.DatabaseException as e:
                await ctx.send(f"Could not set up dynamic rules: {e}")
        else:
            await ctx.send("Dynamic rules is already set up for this server!")

    # ================================
    #    Get Dynamic Rules Settings
    # ================================

    @dynamicrules.group(name="get", invoke_without_command=True)
    @commands.check(checks.permissions(manage_messages=True))
    @commands.check(needs_setup)
    async def dynamicrules_get(self, ctx, *, entry: str):
        """Gets a dynamic rules setting for the server.

        Passing "all" will show all settings."""
        server = ctx.guild
        async with self.bot.db.get_session() as s:
            query = await s.select(tables.Dynamic_Rules).where(tables.Dynamic_Rules.guild_id == server.id).first()
        assert isinstance(query, tables.Dynamic_Rules)
        attrs = json.loads(query.attrs)
        attr_list = [(key, attrs[key]) for key in attrs]
        if len(attr_list) == 0:
            return await ctx.send("You have no Dynamic Rules Overwrites!")
        else:
            await ctx.send(attrs.get(entry, "None"))

    @dynamicrules_get.command(name="all")
    @commands.check(checks.permissions(manage_messages=True))
    @commands.check(needs_setup)
    async def dynamicrules_get_all(self, ctx):
        """Gets all dynamic rules settings for the server."""
        server = ctx.guild
        async with self.bot.db.get_session() as s:
            query = await s.select(tables.Dynamic_Rules).where(tables.Dynamic_Rules.guild_id == server.id).first()
        assert isinstance(query, tables.Dynamic_Rules)
        attrs = json.loads(query.attrs)
        attr_list = [(key, attrs[key]) for key in attrs]
        if len(attr_list) == 0:
            return await ctx.send("You have no Dynamic Rules Overwrites!")
        else:
            await ctx.send(util.neatly(attr_list, "autohotkey"))

    # ================================
    #    Set Dynamic Rules Settings
    # ================================

    def handle_typing(self, entry, value):  # Look, I know this is god awful, but it just works™
        valid_dict = self.valid_settings
        valid = [k for k in valid_dict]
        if entry not in valid:
            valid = ", ".join(valid)
            return None, f"Sorry, but the only valid settings are: {valid}"
        value_type = valid_dict[entry]
        if valid_dict[entry] == bool:
            if value.lower() not in ["true", "false"]:
                return None, f"Sorry, but that setting needs to be either `True` or `False`."
            value = value.lower() == 'true'
        else:
            try:
                value = value_type(value)
            except ValueError:
                return None, f"Sorry, but that setting needs to be of type `{str(valid_dict[entry].__name__)}`."
        return value, None

    @dynamicrules.command(name="set")
    @commands.check(checks.permissions(manage_messages=True))
    @commands.check(needs_setup)
    async def dynamicrules_set(self, ctx, entry: str, *, value: str):
        """
        Set a dynamic rules value for the server.
        """
        server = ctx.guild
        try:
            value, error = self.handle_typing(entry, value)
            if error is not None:
                return await ctx.send(error)
            async with self.bot.db.get_session() as s:
                query = await s.select(tables.Dynamic_Rules).where(tables.Dynamic_Rules.guild_id == server.id).first()
                assert isinstance(query, tables.Dynamic_Rules)
                attrs = json.loads(query.attrs)
                value = str(value)
                attrs[entry] = value
                query.attrs = json.dumps(attrs)
                await s.add(query)
                await ctx.send(f"Successfully set `{entry}` to `{value}`!")
        except asyncqlio.DatabaseException as e:
            await ctx.send(f"Could not set dynamic rules entry: {e}")

    # ==================================
    #    Clear Dynamic Rules Settings
    # ==================================

    @dynamicrules.group(name="clear", invoke_without_command=True)
    @commands.check(checks.permissions(manage_messages=True))
    @commands.check(needs_setup)
    async def dynamicrules_clear(self, ctx, *, entry: str):
        """
        Clear a dynamic rules entry for the server.

        Passing "all" will clear all settings.
        """
        server = ctx.guild
        try:
            async with self.bot.db.get_session() as s:
                query = await s.select(tables.Dynamic_Rules).where(tables.Dynamic_Rules.guild_id == server.id).first()
                assert isinstance(query, tables.Dynamic_Rules)
                attrs = json.loads(query.attrs)
                try:
                    del attrs[entry]
                except KeyError:
                    return await ctx.send(f"You have no entry named `{entry}`!")
                query.attrs = json.dumps(attrs)
                await s.add(query)
            await ctx.send(f"Successfully cleared `{entry}`!")
        except asyncqlio.DatabaseException as e:
            await ctx.send(f"Could not clear dynamic rules entry: {e}")

    @dynamicrules_clear.group(name="all")
    @commands.check(checks.permissions(manage_messages=True))
    @commands.check(needs_setup)
    async def dynamicrules_clear_all(self, ctx):
        """
        Clears all dynamic rules entries for the server.

        Careful, this action is IRREVERSIBLE!
        """
        await ctx.send("Are you sure you want to clear *all* entries? This action is IRREVERSIBLE! "
                       "If yes, type `yes` in 10 seconds, or the action will be aborted.")

        def check(m):
            return m.author == ctx.author and m.content.lower() == "yes"

        try:
            await ctx.bot.wait_for("message", check=check, timeout=10)
        except asyncio.TimeoutError:
            return await ctx.send("Timeout limit reached, aborting.")
        server = ctx.guild
        try:
            async with self.bot.db.get_session() as s:
                query = await s.select(tables.Dynamic_Rules).where(tables.Dynamic_Rules.guild_id == server.id).first()
                assert isinstance(query, tables.Dynamic_Rules)
                attrs = {}
                query.attrs = json.dumps(attrs)
                await s.add(query)
                await ctx.send("Successfully cleared all entries!")
        except asyncqlio.DatabaseException as e:
            await ctx.send(f"Could not clear all dynamic rules entries: {e}")


def setup(bot: DiscordBot):
    bot.add_cog(DynamicRules(bot))
