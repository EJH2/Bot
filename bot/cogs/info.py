# coding=utf-8
"""File containing informative commands for the bot"""
import inspect
import random
import re
import sys
import textwrap
import time
from collections import Counter, OrderedDict

import discord
from discord.ext import commands

from bot.main import Bot
from bot.utils.utils import SourceEntity, InviteUserGuild, neatly


class Info:
    """Cog containing informative commands for the bot"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def source(self, ctx, *, entity: SourceEntity):
        """Gets the source of the requested entity."""
        code = inspect.getsource(entity)
        code = textwrap.dedent(code).replace('`', '\u200b`')
        await ctx.send(f'```py\n{code}\n```')

    @commands.command(aliases=['alert'])
    async def suggest(self, ctx, *, suggestion: str):
        """Sends a message to the bot owner with your suggestion!"""
        await self.bot.app_info.owner.send(f'Suggestion received from {ctx.author} (ID: {ctx.author.id}) in {ctx.guild}'
                                           f' (ID: {ctx.guild.id}): {suggestion}')
        await ctx.send(f'{ctx.author.mention}, your suggestion has been sent to the owner!')

    @commands.command()
    async def lookup(self, ctx, *, id_number: InviteUserGuild):
        """Looks up an ID for a guild, user, or invite."""
        if isinstance(id_number, discord.Invite):
            inv = id_number
            embed = discord.Embed(title=f'Invite Code {inv.code}')
            inviter = f"{inv.inviter} ({inv.inviter.id})" if inv.inviter else "None"
            icon = inv.guild.icon_url_as(format='png') if isinstance(inv.guild, discord.Guild) else None
            embed.add_field(name='Statistics:',
                            value=f'Guild: {inv.guild.name} ({inv.guild.id})\n'
                                  f'Channel: #{inv.channel.name} ({inv.channel.id})\n'
                                  f'Created By: {inviter}')
            embed.set_thumbnail(url=icon) if icon is not None else None
            return await ctx.send(embed=embed)
        if isinstance(id_number, discord.User):
            user = id_number
            embed = discord.Embed(title=str(user))
            embed.add_field(name='Statistics:',
                            value=f'ID: {user.id}\n'
                                  f'Created At: {user.created_at}\n'
                                  f'Bot: {user.bot}')
            embed.set_thumbnail(url=id_number.avatar_url_as(static_format='png'))
            return await ctx.send(embed=embed)
        else:
            json = dict(id_number)
            if json['data_type'] == 'guild':
                rx = r'(?:https?\:\/\/)?(?:[a-zA-z]+\.)?discordapp\.com\/invite\/(.+)'
                m = re.match(rx, json['instant_invite'])
                _invite = m.group(1)
                invite = await commands.InviteConverter().convert(ctx, _invite)
                assert isinstance(invite, discord.Invite)
                i = invite.uses if invite is not None else "No"
                embed = discord.Embed(title=json['name'])
                embed.add_field(name='Statistics',
                                value=f'Voice Channels: {len(json["channels"])}\n'
                                      f'Creation Date: {discord.utils.snowflake_time(int(json["id"]))}\n'
                                      f'Members: {len(json["members"])}\n'
                                      f'Invite: **{_invite}** #{invite.channel.name} ({invite.channel.id}), {i} Uses')
                return await ctx.send(embed=embed)
            elif json['data_type'] == 'guild_partial':
                return await ctx.send(f'Guild with ID {json["id"]} found, no other info found.')

    @commands.command()
    async def info(self, ctx, user: discord.User = None):
        """Gets information about a Discord user."""
        if user is None:
            user = ctx.author
        shared = str(len([i for i in ctx.bot.guilds if i.get_member(user.id)]))
        em = discord.Embed(title=f'Information for {user.display_name}:')
        em.add_field(name='Name:', value=user.name)
        em.add_field(name='Discriminator:', value=user.discriminator)
        em.add_field(name='ID:', value=user.id)
        em.add_field(name='Bot:', value=user.bot)
        em.add_field(name='Created At:', value=user.created_at)
        em.add_field(name='Shared Servers:', value=shared)
        em.add_field(name='Avatar URL:', value=user.avatar_url)
        em.set_thumbnail(url=user.avatar_url_as(static_format='png'))
        await ctx.send(embed=em)

    @commands.group(invoke_without_command=True, aliases=["stats"])
    async def about(self, ctx):
        """Gives information about the bot."""
        revision = self.bot.revisions
        owner = self.bot.app_info.owner
        seconds = time.time() - self.bot.start_time
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        w, d = divmod(d, 7)
        unique_members = set(self.bot.get_all_members())
        unique_online = sum(1 for m in unique_members if m.status != discord.Status.offline)
        perms = discord.Permissions(470150343)
        url = discord.utils.oauth_url(self.bot.app_info.id, perms)

        def calc_max_values(c: Counter, cmd: str, optional_msg: str = None):
            """Calculate max values for a Counter"""
            try:
                max_value = max(c.values())
                used = [(key, c[key]) for key in c if c[key] == max_value]
                if len(used) > 3:
                    most_used = f"See `{self.bot.command_prefix}info {cmd}`"
                else:
                    most_used = ", ".join([f"{str(x[0])} - {str(x[1])}" + (f" {optional_msg}" if optional_msg else "")
                                           for x in used])
            except ValueError:
                most_used = "None"
            return most_used

        cmd_used, cmd_used_in = calc_max_values(self.bot.commands_used, "commands"), \
            calc_max_values(self.bot.commands_used_in, "servers", "commands run")
        u_s = "s" if len(cmd_used.split(",")) > 1 else ""
        ui_s = "s" if len(cmd_used_in.split(",")) > 1 else ""
        em = discord.Embed(description=str('**Latest Changes:**\n' + revision) if revision else None)
        em.title = "Bot Invite Link"
        em.url = url
        em.set_thumbnail(url=self.bot.user.avatar_url)
        em.set_author(name="Owned by: " + str(owner), icon_url=owner.avatar_url)
        em.add_field(name="Library:", value="[Discord.py](https://github.com/Rapptz/discord.py)"
                                            f" (Python {sys.version_info[0]}.{sys.version_info[1]}."
                                            f"{sys.version_info[2]})")
        em.add_field(name="Servers:", value=str(len(ctx.bot.guilds)))
        em.add_field(name="Up-time:", value=f"{int(w)}w : {int(d)}d : {int(h)}h : {int(m)}m : {int(s)}s")
        em.add_field(name="Total Unique Users:", value=f"{len(unique_members)} ({unique_online} online)")
        em.add_field(name=f"Most Used Command{u_s}", value=str(cmd_used))
        em.add_field(name=f"Most Active Server{ui_s}", value=str(cmd_used_in))
        await ctx.send(embed=em)

    @staticmethod
    def calc_popularity(c: Counter, msg: str = None):
        """Calculate the popularity of items in a Counter"""
        cmd_msg = {}
        used = OrderedDict(c.most_common())
        if used:
            for k, v in used.items():
                cmd_msg[str(k)] = str(v) + " uses"
        else:
            cmd_msg["None"] = "No commands seemed to have been run yet!" if not msg else msg
        return cmd_msg

    @about.command(name="commands")
    async def about_commands(self, ctx):
        """Gives info on how many commands have been used."""
        em = discord.Embed(title="Command Statistics", description=neatly(
            entries=self.calc_popularity(self.bot.commands_used), colors="autohotkey"))
        await ctx.send(embed=em)

    @about.command(name="servers", aliases=["guilds"])
    async def about_servers(self, ctx):
        """Gives info on the most popular servers by command usage"""
        em = discord.Embed(title="Server Statistics", description=neatly(
            entries=self.calc_popularity(self.bot.commands_used_in), colors="autohotkey"))
        await ctx.send(embed=em)

    @commands.command()
    async def ping(self, ctx):
        """Pings the bot."""
        joke = random.choice(["not actually pinging server...", "hey bb", "what am I doing with my life",
                              "Some Dragon is a dank music bot tbh", "I'd like to thank the academy for this award",
                              "The NSA is watching 👀", "`<Insert clever joke here>`", "¯\_(ツ)_/¯", "(づ｡◕‿‿◕｡)づ",
                              "I want to believe...", "Hypesquad is a joke", "EJH2#0330 is my daddy", "Robino pls",
                              "Seth got arrested again...", "Maxie y u do dis", "aaaaaaaaaaaAAAAAAAAAA", "owo",
                              "uwu", "meme team best team", "made with dicksword dot pee why", "I'm running out of "
                                                                                               "ideas here",
                              "am I *dank* enough for u?", "this is why we can't have nice things. come on",
                              "You'll understand when you're older...", "\"why\", you might ask? I do not know...",
                              "I'm a little tea pot, short and stout", "I'm not crying, my eyeballs "
                                                                       "are sweating!",
                              "When will the pain end?", "Partnership when?", "Hey Robino, rewrite when?"])
        before = time.monotonic()
        ping_msg = await ctx.send("Pinging Server...")
        after = time.monotonic()
        ping = (after - before) * 1000
        await ping_msg.edit(content=joke + f" // ***{ping:.0f}ms***")

    @commands.command(aliases=["oauth", "invite"])
    async def join(self, ctx):
        """Gives my OAuth url."""
        perms = discord.Permissions(470150343)
        await ctx.send(discord.utils.oauth_url(self.bot.app_info.id, perms))


def setup(bot: Bot):
    """Setup function for the cog"""
    bot.add_cog(Info(bot))
