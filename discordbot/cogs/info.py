"""
Informative commands.
"""

import copy
import sys
import time
from collections import Counter

import discord
import markovify
from discord.ext import commands

from discordbot import consts
from discordbot.bot import DiscordBot
from discordbot.cogs.utils import checks, config, util, exceptions


class Information:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    def __global_check(self, ctx):
        self.config = config.Config("ignored.yaml")

        author = ctx.message.author
        if commands.is_owner():
            return True

        # user is a bot
        if author.bot:
            return False

        # user is blacklisted
        if author.id in self.config.get("users"):
            return False

        perms = ctx.message.channel.permissions_for(author)
        perm_list = [perms.administrator, perms.manage_messages, perms.manage_guild]
        un_ignore = any(x for x in perm_list)

        # now we can finally realise if we can actually bypass the ignore
        if not un_ignore and ctx.message.channel.id in self.config.get("channels"):
            raise exceptions.Ignored

        return True

    # ========================
    #   Bot related commands
    # ========================

    @commands.group(aliases=["stats"])
    @commands.check(checks.needs_embed)
    async def info(self, ctx):
        """
        Gives information about the bot.
        """
        if ctx.invoked_subcommand is None:
            app_info = await self.bot.application_info()
            owner = app_info.owner
            seconds = time.time() - consts.start
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)
            w, d = divmod(d, 7)
            unique_members = set(self.bot.get_all_members())
            unique_online = sum(1 for m in unique_members if m.status != discord.Status.offline)
            channel_types = Counter(type(c) for c in self.bot.get_all_channels())
            voice = channel_types[discord.channel.VoiceChannel]
            text = channel_types[discord.channel.TextChannel]
            perms = discord.Permissions.none()
            perms.administrator = True
            url = discord.utils.oauth_url(app_info.id, perms)
            try:
                c = self.bot.commands_used
                max_value = max(c.values())
                commands_used = [(key, c[key]) for key in c if c[key] == max_value]
                if len(commands_used) > 3:
                    most_used = "See `{}info commands`".format(self.bot.command_prefix)
                else:
                    most_used = ", ".join([str(x[0]) + " - " + str(x[1]) for x in commands_used])
            except ValueError:
                most_used = "None"

            em = discord.Embed(description="Bot Stats:")
            em.title = "Bot Invite Link"
            em.url = url
            em.set_thumbnail(url=self.bot.user.avatar_url)
            em.set_author(name="Owned by: " + str(owner), icon_url=owner.avatar_url)
            em.add_field(name="Library:", value="[Discord.py](https://github.com/Rapptz/discord.py)"
                                                " (Python {0.version_info[0]}.{0.version_info[1]}."
                                                "{0.version_info[2]})".format(sys))
            em.add_field(name="Bot Version:", value="[{0.bot_config[bot][version]}](!!!! '{0.bot_config[bot][codename]}"
                                                    "')".format(consts))
            em.add_field(name="Servers:", value=str(len(ctx.bot.guilds)))
            em.add_field(name="Up-time:", value="{}w : {}d : {}h : {}m : {}s".format(int(w), int(d), int(h), int(m),
                                                                                     int(s)))
            em.add_field(name="Total Unique Users:", value="{} ({} online)".format(len(unique_members), unique_online))
            em.add_field(name="Text Channels:", value=str(text))
            em.add_field(name="Voice Channels:", value=str(voice))
            em.add_field(name="Most Used Commands", value=str(most_used))
            await ctx.send(embed=em)

    @info.command(aliases=["commands"])
    async def commands_used(self, ctx):
        """
        Gives info on how many commands have been used.
        """
        msg = []
        if dict(self.bot.commands_used):
            for k, v in dict(ctx.bot.commands_used).items():
                msg.append((str(k), str(v) + " uses"))
        else:
            msg = [("None", "No commands seemed to have been run yet!")]
        await ctx.send(embed=discord.Embed(title="Commands Run:", description=util.neatly(
                           entries=msg, colors="autohotkey")))

    @commands.command()
    async def ping(self, ctx):
        """
        Pings the bot.
        """
        with open("discordbot/cogs/utils/files/markov.txt") as file:
            markov_text = file.read()
        markov = markovify.Text(markov_text)
        joke = None
        while joke is None:
            joke = markov.make_sentence()
        ping_time = time.time()
        ping_msg = await ctx.send("Pinging Server...")
        ping = time.time() - ping_time
        await ping_msg.edit(content=joke + " // ***%.01f secs***" % ping)

    # ===========================
    #   Player related commands
    # ===========================

    @commands.command(aliases=["oauth"])
    async def join(self, ctx):
        """
        Gives my OAuth url.
        """
        app_info = await self.bot.application_info()
        app_id = str(app_info.id)
        perms = discord.Permissions.none()
        perms.administrator = True
        await ctx.send(discord.utils.oauth_url(app_id, perms))

    @commands.command(aliases=["playerstats", "player", "userinfo", "userstats", "user"])
    async def playerinfo(self, ctx, *, user: discord.Member = None):
        """
        Gives you player info on a user. If a user isn"t passed then the shown info is yours.
        """
        if not user:
            user = ctx.message.author

        roles = [role.name.replace("@", "@\u200b") for role in user.roles]
        share = sum(1 for m in self.bot.get_all_members() if m.id == user.id)
        voice_channel = user.voice
        if voice_channel is not None:
            voice_channel = voice_channel.channel.name
        else:
            voice_channel = "Not in a voice channel."

        msg = [
            ("Name", user.name),
            ("Discrim", user.discriminator),
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
        """
        Gives information about the current server.
        """
        server = ctx.message.guild

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
            ("Default Channel", server.default_channel),
            ("Members", member_list.format(len(server.members), member_by_status)),
            ("Text Channels", text_list.format(text_channels, secret_channels)),
            ("Voice Channels", voice_list.format(voice_channels, secret_voice)),
            ("Icon", server.icon_url),
            ("Roles", ", ".join(roles))
        ]

        await ctx.send(util.neatly(msg))

    @commands.command()
    async def avatar(self, ctx, *, member: discord.Member = None):
        """
        Shows a members avatar.
        """
        if not member:
            member = ctx.message.author

        await ctx.send("The avatar of {} is: {}".format(member.name, member.avatar_url))

    @commands.command()
    async def discrim(self, ctx, discrim: int = None):
        """
        Shows other people with your discriminator.
        """
        if not discrim:
            discrim = int(ctx.message.author.discriminator)
        disc = []
        for server in ctx.bot.guilds:
            for member in server.members:
                if int(member.discriminator) == discrim:
                    if member.name not in disc:
                        disc.append(member.name)
        await ctx.send("```\n{}\n```".format(", ".join(disc)))


def setup(bot: DiscordBot):
    bot.add_cog(Information(bot))
