"""
Salty commands, require the bot to have the role "Salty" to use.
"""
import json
import random

import discord
import urbandictionary as ud
from discord.ext import commands

from discordbot.main import DiscordBot
from discordbot.utils import checks


class Salty:
    """
    Salty commands, require the bot to have the role "Salty" to use.
    """

    def __init__(self, bot: DiscordBot):
        self.bot = bot
        with open("discordbot/files/text/insults.json") as insults:
            self.insult_words = json.load(insults)

    @commands.command()
    @commands.check(checks.bot_roles("salty"))
    async def insult(self, ctx, user: str = None):
        """Insults a user."""
        name = f"{str(user) + ': ' or ''}"

        words_list = [self.insult_words['A'], self.insult_words['B'], self.insult_words['C'], self.insult_words['D'],
                      self.insult_words['E'], self.insult_words['F']]
        insult = [random.choice(i) for i in words_list]

        # The one case where using .format is better and shorter than a format string
        await ctx.send("{} You are {} {} {} and a {} {} {}.".format(name, *insult))

    @commands.command()
    @commands.check(checks.bot_roles("salty"))
    @commands.check(checks.needs_embed)
    async def urband(self, ctx, query: str, page: int = None):
        """Finds a phrase in the Urban Dictionary."""
        resp = await ud.define(query)
        if resp:
            if page:
                term = resp[page-1]
            else:
                term = resp[0]
            em = discord.Embed(color=0x2EAE48)
            em.title = term.word
            em.url = term.permalink
            em.description = term.definition
            em.add_field(name="Example", value=term.example if len(term.example) < 0 else "None")
            em.set_footer(text="Author: {}".format(term.author))
            em.timestamp = ctx.message.created_at
            await ctx.send(embed=em)
        else:
            em = discord.Embed(color=discord.Color.red())
            em.title = "\N{CROSS MARK} Error"
            em.description = "Either the page doesn't exist, or you typed it in wrong. Either way, please try again."
            await ctx.send(embed=em)


def setup(bot: DiscordBot):
    bot.add_cog(Salty(bot))
