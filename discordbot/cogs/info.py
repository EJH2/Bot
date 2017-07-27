"""
Informative commands.
"""

import copy
import random
import sys
import time
from collections import Counter, OrderedDict

import discord
from discord.ext import commands

from discordbot.bot import DiscordBot
from discordbot.cogs.utils import checks, config, util, exceptions
from discordbot.consts import bot_config, start


class Information:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    def __global_check(self, ctx):
        self.config = config.Config("ignored.yaml")

        author = ctx.author
        if commands.is_owner():
            return True

        # user is a bot
        if author.bot:
            return False

        # user is blacklisted
        if author.id in self.config.get("users"):
            return False

        perms = ctx.channel.permissions_for(author)
        perm_list = [perms.administrator, perms.manage_messages, perms.manage_guild]
        un_ignore = any(x for x in perm_list)

        # now we can finally realise if we can actually bypass the ignore
        if not un_ignore and ctx.channel.id in self.config.get("channels"):
            raise exceptions.Ignored

        return True

    # ========================
    #   Bot related commands
    # ========================

    @commands.command()
    async def alert(self, ctx, *, message):
        """
        Sends a message to my developer! (Use only to report bugs. Abuse will get you bot banned!)
        """
        await ctx.bot.owner.send(f"New message from {ctx.author.name}#{ctx.author.discriminator}"
                                 f" ({ctx.author.id}) in {ctx.guild.name}: {message}")

    @commands.group(invoke_without_command=True, aliases=["stats"])
    @commands.check(checks.needs_embed)
    async def info(self, ctx):
        """
        Gives information about the bot.
        """
        app_info = await self.bot.application_info()
        owner = ctx.bot.owner
        seconds = time.time() - start
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
                most_used = f"See `{self.bot.command_prefix_}info commands`"
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
                                            f" (Python {sys.version_info[0]}.{sys.version_info[1]}."
                                            f"{sys.version_info[2]})")
        if None not in [bot_config["bot"]["version"], bot_config["bot"]["codename"]]:
            em.add_field(name="Bot Version:", value=f"[{bot_config['bot']['version']}]"
                                                    f"(!!!! '{bot_config['bot']['codename']}')")
        em.add_field(name="Servers:", value=str(len(ctx.bot.guilds)))
        em.add_field(name="Up-time:", value=f"{int(w)}w : {int(d)}d : {int(h)}h : {int(m)}m : {int(s)}s")
        em.add_field(name="Total Unique Users:", value=f"{len(unique_members)} ({unique_online} online)")
        em.add_field(name="Text Channels:", value=str(text))
        em.add_field(name="Voice Channels:", value=str(voice))
        em.add_field(name="Most Used Commands", value=str(most_used))
        em.add_field(name="Support Server", value="Click [**here**](https://discord.gg/4fKgwPn 'Gears of Bots') to stay"
                                                  " updated on all the latest news!", inline=False)
        await ctx.send(embed=em)

    @info.command(aliases=["commands"])
    async def commands_used(self, ctx):
        """
        Gives info on how many commands have been used.
        """
        msg = []
        used = OrderedDict(self.bot.commands_used.most_common())
        if used:
            for k, v in used.items():
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
        Gives you player info on a user. If a user isn't passed then the shown info is yours.
        """
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
        """
        Gives information about the current server.
        """
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
            member = ctx.author

        await ctx.send(f"The avatar of {member.name} is: {member.avatar_url_as(static_format='png')}")

    @commands.command()
    async def discrim(self, ctx, discrim: int = None):
        """
        Shows other people with your discriminator.
        """
        if not discrim:
            discrim = int(ctx.author.discriminator)
        disc = []
        for server in ctx.bot.guilds:
            for member in server.members:
                if int(member.discriminator) == discrim:
                    if member.name not in disc:
                        disc.append(member.name)
        await ctx.send(f"```\n{', '.join(disc)}\n```")


def setup(bot: DiscordBot):
    bot.add_cog(Information(bot))
