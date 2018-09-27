"""
Stupid commands for the bot.
"""
import io
import random
from urllib.parse import quote_plus

from discord.ext import commands

from discordbot.main import DiscordBot


class Stupid:
    """
    Stupid commands for the bot.
    """

    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.command()
    async def lmgtfy(self, ctx, *, query: str):
        """Gives the user a "Let Me Google That For You" link."""
        await ctx.send(f"http://lmgtfy.com/?q={quote_plus(query)}")

    @commands.command()
    async def shame(self, ctx):
        """Let the shame bells ring!"""
        await ctx.send(":bell::bell::bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ "
                       "​:bell: ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​:bell:"
                       " ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​:bell::bell:"
                       ":bell:\n:bell: ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​:bell:"
                       " ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell:"
                       " ​ ​ ​ ​ ​ ​ ​:bell::bell::bell::bell: ​ ​ ​ ​ ​ ​:bell:\n:bell:"
                       ":bell::bell: ​ ​ ​ ​ ​ ​ ​:bell::bell::bell:"
                       " ​ ​ ​ ​ ​ ​ ​:bell::bell::bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​:bell:"
                       " ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell::bell::bell:\n"
                       "              :bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell:"
                       " ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ "
                       "​ ​ ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell:\n:bell::bell:"
                       ":bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​:bell:"
                       " ​ ​ ​ ​ ​ ​ ​:bell: ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​ ​:bell:"
                       " ​ ​ ​ ​ ​ ​ ​:bell::bell:​:bell:\n")

    @commands.command()
    async def copypasta(self, ctx, query: int = None):
        """Gives the user a random copypasta.

        Do `copypasta <number from 1-22>` for a specific copypasta!
        """
        with io.open('discordbot/files/text/copypasta.txt', 'r', encoding='utf8') as f:
            data = f.readlines()
        if query:
            query_req = 1 <= query <= len(data)
            line = f"Query must be from 1 to {len(data)}!"
            if query_req:
                line = data[query - 1]
        else:
            line = random.choice(data)
        await ctx.send(line)

    @commands.command()
    async def roti(self, ctx, *, number: int = None):
        """Bestows the user with the Rules of the Internet.

        If no number is provided, then a random rule will be retrieved."""
        with io.open('discordbot/files/text/RulesOTI.txt', 'r', encoding='utf8') as f:
            data = f.readlines()
        if number:
            query_req = 1 <= number <= len(data)
            line = f"Number must be from 1 to {len(data)}!"
            if query_req:
                line = data[number - 1]
        else:
            line = random.choice(data)
        await ctx.send(line)

    @commands.command()
    async def discrim(self, ctx, discrim: int = None):
        """Shows other people with your discriminator."""
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
    bot.add_cog(Stupid(bot))
