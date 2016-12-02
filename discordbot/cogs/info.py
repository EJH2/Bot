"""
Informative commands.
"""

import copy
import sys
import time
from collections import Counter

import aiohttp
import discord
from bs4 import BeautifulSoup as Soup
from discord.ext import commands

from discordbot import consts
from discordbot.bot import DiscordBot
from discordbot.cogs.utils import checks, config, util, exceptions


class Information:
    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.config = config.Config("ignored.yaml")

    def __check(self, ctx):
        author = ctx.message.author
        if checks.is_owner(ctx):
            return True

        # user is a bot
        if author.bot:
            return False

        # user is blacklisted
        if author.id in self.config.get("users"):
            return False

        perms = ctx.message.channel.permissions_for(author)
        perm_list = [perms.administrator, perms.manage_messages, perms.manage_server]
        un_ignore = any(x for x in perm_list)

        # now we can finally realise if we can actually bypass the ignore
        if not un_ignore and ctx.message.channel.id in self.config.get("channels"):
            raise exceptions.Ignored

        return True

    # ========================
    #   Bot related commands
    # ========================

    @commands.group(aliases=["stats"], pass_context=True)
    async def info(self, ctx):
        """
        Gives information about the bot.
        """
        if ctx.invoked_subcommand is None:
            app_info = await self.bot.application_info()
            owner = str(app_info.owner)
            seconds = time.time() - consts.start
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)
            w, d = divmod(d, 7)
            unique_members = set(self.bot.get_all_members())
            unique_online = sum(1 for m in unique_members if m.status != discord.Status.offline)
            channel_types = Counter(c.type for c in self.bot.get_all_channels())
            voice = channel_types[discord.ChannelType.voice]
            text = channel_types[discord.ChannelType.text]
            try:
                c = self.bot.commands_used
                max_value = max(c.values())
                commands_used = [(key, c[key]) for key in c if c[key] == max_value]
                most_used = ", ".join([str(x[0]) + " - " + str(x[1]) for x in commands_used])
            except ValueError:
                most_used = "None"

            msg = ["```swift",
                   "Stats:",
                   "           Developer: {} (ID: 125370065624236033)".format(owner),
                   "             Library: Discord.py (Python {0.version_info[0]}.{0.version_info[1]}."
                   "{0.version_info[2]})".format(sys),
                   "         Bot Version: {}".format(consts.bot_config["bot"]["version"]),
                   "             Servers: {}".format(len(self.bot.servers)),
                   "              Uptime: {}w : {}d : {}h : {}m : {}s".format(int(w), int(d), int(h), int(m), int(s)),
                   "  Total Unique Users: {} ({} online)".format(len(unique_members), unique_online),
                   "       Text Channels: {}".format(text),
                   "      Voice Channels: {}".format(voice),
                   "Most Used Command(s): {} (see {}info commands for more stats)".format(most_used,
                                                                                          self.bot.command_prefix),
                   "```"]

            await self.bot.say("\n".join(msg))

    @info.command(aliases=["commands"])
    async def commands_used(self):
        """
        Gives info on how many commands have been used.
        """
        msg = []
        for k, v in dict(self.bot.commands_used).items():
            msg.append((str(k), str(v) + " uses"))
        await self.bot.say(util.neatly(entries=msg, colors="autohotkey"))

    @commands.command()
    async def ping(self):
        """
        Pings the bot.
        """
        url = "http://www.codingexcuses.com/"
        with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                r = await resp.read()
        resp = Soup(r, 'html.parser')
        joke = resp.find('div', {'class': 'wrapper'}).text.strip("\n")
        ping_time = time.time()
        ping_msg = await self.bot.say("Pinging Server...")
        ping = time.time() - ping_time
        await self.bot.edit_message(ping_msg, joke + " // ***%.01f secs***" % ping)

    # ===========================
    #   Player related commands
    # ===========================

    @commands.command(aliases=["oauth"])
    async def join(self):
        """
        Gives my OAuth url.
        """
        app_info = await self.bot.application_info()
        app_id = str(app_info.id)
        perms = discord.Permissions.none()
        perms.read_messages = True
        perms.send_messages = True
        perms.manage_roles = True
        perms.ban_members = True
        perms.kick_members = True
        perms.manage_messages = True
        perms.embed_links = True
        perms.read_message_history = True
        perms.attach_files = True
        perms.administrator = True
        await self.bot.say(discord.utils.oauth_url(app_id, perms))

    @commands.command(pass_context=True, aliases=["playerstats", "player", "userinfo", "userstats", "user"])
    async def playerinfo(self, ctx, *, user: discord.User = None):
        """
        Gives you player info on a user. If a user isn"t passed then the shown info is yours.
        """
        if not user:
            user = ctx.message.author

        roles = [role.name.replace("@", "@\u200b") for role in user.roles]
        share = sum(1 for m in self.bot.get_all_members() if m.id == user.id)
        voice_channel = user.voice_channel
        if voice_channel is not None:
            voice_channel = voice_channel.name
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

        await self.bot.say(util.neatly(msg))

    @commands.command(pass_context=True, aliases=["serverstats", "serverdata", "server"])
    async def serverinfo(self, ctx):
        """
        Gives information about the current server.
        """
        server = ctx.message.server

        roles = [role.name.replace("@", "@\u200b") for role in server.roles]

        member = copy.copy(server.me)
        member.id = "0"
        member.roles = [server.default_role]

        secret_channels = 0
        secret_voice = 0
        text_channels = 0
        for channel in server.channels:
            perms = channel.permissions_for(member)
            is_text = channel.type == discord.ChannelType.text
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

        await self.bot.say(util.neatly(msg))

    @commands.command(pass_context=True)
    async def avatar(self, ctx, *, member: discord.Member = None):
        """
        Shows a members avatar.
        """
        if not member:
            member = ctx.message.author

        await self.bot.say("The avatar of {} is: {}".format(member.name, member.avatar_url))

    @commands.command(pass_context=True)
    async def discrim(self, ctx, discrim: int = None):
        """
        Shows other people with your discriminator.
        """
        if discrim is not None:
            discrim = discrim
        else:
            discrim = int(ctx.message.author.discriminator)
        disc = []
        for server in self.bot.servers:
            for member in server.members:
                if int(member.discriminator) == discrim:
                    if member.name not in disc:
                        disc.append(member.name)
        await self.bot.say("```\n{}\n```".format(", ".join(disc)))

    @commands.command(pass_context=True)
    async def test(self, ctx, message):
        embed = discord.Embed(title="Look at this", color=discord.Color(0xFFF000), url="https://ejh2.me")
        embed.set_author(name=message, url="https://ejh2.me", icon_url=ctx.message.author.avatar_url)
        await self.bot.say(content="Check it", embed=embed)


def setup(bot: DiscordBot):
    bot.add_cog(Information(bot))
