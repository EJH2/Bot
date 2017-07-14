import aiohttp

from discordbot.consts import bot_config


class Stats:
    """
    Cog for updating the https://bots.discord.pw bot information.
    """

    def __init__(self, bot):
        self.bot = bot

    async def update(self):
        stats = {'server_count': len(self.bot.guilds)}
        token = bot_config.get("bots_pw_token", None)
        if not token:
            return

        session = aiohttp.ClientSession()

        url = 'https://bots.discord.pw/api/bots/{}/stats'.format(self.bot.user.id)
        headers = {'Authorization': token, 'Content-Type': 'application/json'}
        async with session.post(url, data=stats, headers=headers) as resp:
            self.bot.logger.info('DBots statistics returned {0.status} for {1}'.format(resp, stats))
        await session.close()

    async def on_guild_join(self, guild):
        await self.update()

    async def on_guild_remove(self, guild):
        await self.update()

    async def on_ready(self):
        await self.update()

    async def on_resume(self):
        await self.update()


def setup(bot):
    bot.add_cog(Stats(bot))
