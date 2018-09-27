"""
Informative commands for the bot.
"""
import asyncio
import copy
import datetime
import inspect
import random
import sys
import textwrap
import time
from collections import Counter, OrderedDict

import babel.dates
import dateutil.parser
import discord
from discord.ext import commands

from discordbot.main import DiscordBot
from discordbot.utils import checks, util


class SourceEntity(commands.Converter):
    async def convert(self, ctx, arg):
        cmd = ctx.bot.get_command(arg)
        if cmd is not None:
            return cmd.callback

        cog = ctx.bot.get_cog(arg)
        if cog is not None:
            return cog.__class__

        module = ctx.bot.extensions.get(arg)
        if module is not None:
            return module

        raise commands.BadArgument(f'{arg} is neither a command, a cog, nor an extension.')


class Information:
    """
    Informative commands for the bot.
    """

    def __init__(self, bot: DiscordBot):
        self.bot = bot

    # ========================
    #   Bot related commands
    # ========================

    @commands.command()
    async def alert(self, ctx, *, message):
        """Sends a message to my developer! (Use only to report bugs. Abuse will get you bot banned!)"""
        guild = "Private Messages"
        if ctx.guild:
            guild = ctx.guild.name
        await ctx.bot.owner.send(f"New message from {ctx.author.name}#{ctx.author.discriminator}"
                                 f" ({ctx.author.id}) in {guild}: {message}")

    @commands.command()
    async def uptime(self, ctx):
        """Gives the bot's uptime."""
        seconds = time.time() - self.bot.start_time
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        w, d = divmod(d, 7)
        await ctx.send(f"I've been online for `{int(w)}w : {int(d)}d : {int(h)}h : {int(m)}m : {int(s)}s`")

    @commands.group(invoke_without_command=True, aliases=["stats"])
    @commands.check(checks.needs_embed)
    async def info(self, ctx):
        """Gives information about the bot."""
        commit_list = []
        async with self.bot.session.get("https://api.github.com/repos/EJH2/ViralBot/commits") as get:
            commits = await get.json()
        for i in range(0, 3):
            tag = commits[i]['sha'][:7]
            message = commits[i]['commit']['message']
            _commit_time = commits[i]['commit']['author']['date']
            delta = dateutil.parser.parse(_commit_time).replace(tzinfo=None) - datetime.datetime.utcnow()
            commit_time = babel.dates.format_timedelta(delta, locale='en_US', add_direction=True)
            commit = f"[`{tag}`](https://github.com/EJH2/ViralBot/commit/{tag}) {message} ({commit_time})"
            commit_list.append(commit)
        revision = '\n'.join(commit_list)
        app_info = await self.bot.application_info()
        owner = ctx.bot.owner
        seconds = time.time() - self.bot.start_time
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        w, d = divmod(d, 7)
        unique_members = set(self.bot.get_all_members())
        unique_online = sum(1 for m in unique_members if m.status != discord.Status.offline)
        channel_types = Counter(type(c) for c in self.bot.get_all_channels())
        voice = channel_types[discord.channel.VoiceChannel]
        text = channel_types[discord.channel.TextChannel]
        perms = discord.Permissions(470083623)
        url = discord.utils.oauth_url(app_info.id, perms)

        def calc_max_values(c: Counter, cmd: str, optional_msg: str = None):
            try:
                max_value = max(c.values())
                used = [(key, c[key]) for key in c if c[key] == max_value]
                if len(used) > 3:
                    most_used = f"See `{self.bot.command_prefix_}info {cmd}`"
                else:
                    most_used = ", ".join([f"{str(x[0])} - {str(x[1])}" + (f" {optional_msg}" if optional_msg else "")
                                           for x in used])
            except ValueError:
                most_used = "None"
            return most_used

        cmd_used, cmd_used_in = calc_max_values(self.bot.commands_used, "commands"), \
                                calc_max_values(self.bot.commands_used_in, "servers", "commands run")
        em = discord.Embed(description='Latest Changes:\n' + revision)
        em.title = "Bot Invite Link"
        em.url = url
        em.set_thumbnail(url=self.bot.user.avatar_url)
        em.set_author(name="Owned by: " + str(owner), icon_url=owner.avatar_url)
        em.add_field(name="Library:", value="[Discord.py](https://github.com/Rapptz/discord.py)"
                                            f" (Python {sys.version_info[0]}.{sys.version_info[1]}."
                                            f"{sys.version_info[2]})")
        if None not in [self.bot.config["bot"]["version"], self.bot.config["bot"]["codename"]]:
            em.add_field(name="Bot Version:", value=f"[{self.bot.config['bot']['version']}]"
                                                    f"(!!!! '{self.bot.config['bot']['codename']}')")
        em.add_field(name="Servers:", value=str(len(ctx.bot.guilds)))
        em.add_field(name="Up-time:", value=f"{int(w)}w : {int(d)}d : {int(h)}h : {int(m)}m : {int(s)}s")
        em.add_field(name="Total Unique Users:", value=f"{len(unique_members)} ({unique_online} online)")
        em.add_field(name="Text Channels:", value=str(text))
        em.add_field(name="Voice Channels:", value=str(voice))
        em.add_field(name="Most Used Commands", value=str(cmd_used))
        em.add_field(name="Most Active Servers", value=str(cmd_used_in))
        em.add_field(name="Support Server", value="Click [**here**](https://discord.gg/4fKgwPn 'Gears of Bots') to stay"
                                                  " updated on all the latest news!", inline=False)
        await ctx.send(embed=em)

    @staticmethod
    def calc_popularity(c: Counter, msg: str = None):
        cmd_msg = []
        used = OrderedDict(c.most_common())
        if used:
            for k, v in used.items():
                cmd_msg.append((str(k), str(v) + " uses"))
        else:
            cmd_msg = [("None", "No commands seemed to have been run yet!" if not msg else msg)]
        return cmd_msg

    @info.command(name="commands")
    async def info_commands(self, ctx):
        """Gives info on how many commands have been used."""
        em = discord.Embed(title="Command Statistics", description=util.neatly(
            entries=self.calc_popularity(self.bot.commands_used), colors="autohotkey"))
        await ctx.send(embed=em)

    @info.command(name="servers")
    async def info_servers(self, ctx):
        """Gives info on the most popular servers."""
        em = discord.Embed(title="Server Statistics", description=util.neatly(
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

    # ===========================
    #   Player related commands
    # ===========================

    @commands.command(aliases=["oauth", "invite"])
    async def join(self, ctx):
        """Gives my OAuth url."""
        app_info = await self.bot.application_info()
        app_id = str(app_info.id)
        perms = discord.Permissions.none()
        perms.administrator = True
        await ctx.send(discord.utils.oauth_url(app_id, perms))

    @commands.command(aliases=["playerstats", "player", "userinfo", "userstats", "user"])
    async def playerinfo(self, ctx, *, user: discord.Member = None):
        """Gives you player info on a user. If a user isn't passed then the shown info is yours."""
        if not user:
            user = ctx.author

        roles = [role.name.replace("@", "@\u200b") for role in user.roles]
        share = sum(1 for m in self.bot.get_all_members() if m.id == user.id)
        voice_channel = user.voice
        if voice_channel is not None:
            voice_channel = voice_channel.channel.name
        else:
            voice_channel = "Not in a voice channel."

        msg = [
            ("Name", user.name), ("Discrim", user.discriminator),
            ("ID", user.id),
            ("Display Name", user.display_name),
            ("Joined at", user.joined_at),
            ("Created at", user.created_at),
            ("Server Roles", ", ".join(roles)),
            ("Color", user.color),
            ("Status", user.status),
            ("Game", user.game),
            ("Voice Channel", voice_channel),
            ("Servers Shared", share),
            ("Avatar URL", user.avatar_url)
        ]

        await ctx.send(util.neatly(msg))

    @commands.command(aliases=["serverstats", "serverdata", "server"])
    async def serverinfo(self, ctx):
        """Gives information about the current server."""
        server = ctx.guild

        roles = [role.name.replace("@", "@\u200b") for role in server.roles]

        member = copy.copy(server.me)
        member.roles = [server.default_role]

        secret_channels = 0
        secret_voice = 0
        text_channels = 0
        for channel in server.channels:
            perms = channel.permissions_for(member)
            is_text = type(channel) == discord.channel.TextChannel
            text_channels += is_text
            if is_text and not perms.read_messages:
                secret_channels += 1
            elif not is_text and (not perms.connect or not perms.speak):
                secret_voice += 1

        voice_channels = len(server.channels) - text_channels
        member_by_status = Counter(str(m.status) for m in server.members)
        member_list = "{0} ({1[online]} online, {1[idle]} idle, and {1[offline]} offline)"
        text_list = "{} ({} hidden)"
        voice_list = "{} ({} locked)"

        msg = [
            ("Name", server.name),
            ("ID", server.id),
            ("Owner", server.owner),
            ("Region", server.region),
            ("Members", member_list.format(len(server.members), member_by_status)),
            ("Text Channels", text_list.format(text_channels, secret_channels)),
            ("Voice Channels", voice_list.format(voice_channels, secret_voice)),
            ("Icon", server.icon_url),
            ("Roles", ", ".join(roles))
        ]

        await ctx.send(util.neatly(msg))

    @commands.command()
    async def avatar(self, ctx, *, member: discord.User = None):
        """Shows a member's avatar."""
        if not member:
            member = ctx.author

        await ctx.send(f"The avatar of {member.name} is: {member.avatar_url}")

    # ====================
    #    Other Commands
    # ====================

    @commands.command()
    async def timer(self, ctx, seconds: int, *, remember: str = ""):
        """Sets a timer for a user with the option of setting a reminder text."""
        if not remember:
            await ctx.send(f"{ctx.author.mention}, you have set a timer for {seconds} seconds!")
            end_timer = ctx.send(f"{ctx.author.mention}, your timer for {seconds} seconds has expired!")

        else:
            await ctx.send(f"{ctx.author.mention}, I will remind you about `{remember}` in {seconds} seconds!")
            end_timer = ctx.send(f"{ctx.author.mention}, your timer for {seconds} seconds has expired! I was instructed"
                                 f" to remind you about `{remember}`!")

        def check(m):
            return m.author == ctx.author and m.content == f"{ctx.bot.command_prefix_}cancel"

        try:
            timer = await ctx.bot.wait_for("message", check=check, timeout=seconds)
            if timer:
                await ctx.send(f"{ctx.author.mention}, Cancelling your timer...")
        except asyncio.TimeoutError:
            await end_timer
            return

    @commands.command()
    async def source(self, ctx, *, entity: SourceEntity):
        """Posts the source code of a command, cog or extension."""
        code = inspect.getsource(entity)
        code = textwrap.dedent(code).replace('`', '\u200b`')

        if len(code) > 1990:
            paste = await self.bot.get_cog("GhostBin").paste_logs(code, "15m")
            return await ctx.send(f'**Your requested sauce was too stronk. So I uploaded to GhostBin! Hurry, it expires'
                                  f' in 15 minutes!**\n<{paste}>')

        return await ctx.send(f'```py\n{code}\n```')


def setup(bot: DiscordBot):
    bot.add_cog(Information(bot))
