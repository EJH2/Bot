# coding=utf-8
"""File containing salty commands for the bot"""
import json
import random

import discord
from asyncurban import UrbanDictionary, errors
from discord.ext import commands
from bot.main import Bot
from bot.utils import checks


class Salty:
    """Cog containing salty commands for the bot"""
    def __init__(self, bot: Bot):
        self.bot = bot
        self.UD = UrbanDictionary(session=self.bot.session)
        with open("bot/files/insults.json") as insults:
            self.insult_words = json.load(insults)

    @commands.command()
    @checks.bot_has_role("Salty")
    async def insult(self, ctx, user: str = None):
        """Insults a user."""
        name = f"{str(user) + ': ' if user else ''}"

        words_list = [self.insult_words['A'], self.insult_words['B'], self.insult_words['C'], self.insult_words['D'],
                      self.insult_words['E'], self.insult_words['F']]
        insult = [random.choice(i) for i in words_list]

        # The one case where using .format is better and shorter than a format string
        await ctx.send("{} You are {} {} {} and a {} {} {}.".format(name, *insult))

    @commands.command(aliases=["ud"])
    @checks.bot_has_role("Salty")
    async def urband(self, ctx, *, query: str):
        """Finds a phrase in the Urban Dictionary."""
        try:
            term = await self.UD.get_word(query)
            em = discord.Embed(color=0x2EAE48)
            em.title = term.word
            em.url = term.permalink
            em.description = term.definition
            em.set_footer(text="Author: {}".format(term.author))
            em.timestamp = ctx.message.created_at
            await ctx.send(embed=em)
        except errors.WordNotFoundError:
            em = discord.Embed(color=discord.Color.red())
            em.title = "\N{CROSS MARK} Error"
            em.description = "Either the page doesn't exist, or you typed it in wrong. Either way, please try again."
            return await ctx.send(embed=em)
        except errors.UrbanConnectionError:
            await ctx.send("I couldn't connect to the Urban Dictionary API, sorry!")


def setup(bot: Bot):
    """Setup function for the cog"""
    bot.add_cog(Salty(bot))
