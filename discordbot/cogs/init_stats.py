"""
Cog for updating the https://bots.discord.pw bot information.
"""
from discordbot.main import DiscordBot


class Stats:
    """
    Cog for updating the https://bots.discord.pw bot information.
    """

    def __init__(self, bot: DiscordBot):
        self.bot = bot

    async def update(self):
        stats = {'server_count': len(self.bot.guilds)}
        token = self.bot.cog_config.get("bots_pw_key", None)
        if not token:
            return

        url = f'https://bots.discord.pw/api/bots/{self.bot.user.id}/stats'
        headers = {'Authorization': token, 'Content-Type': 'application/json'}
        async with self.bot.session.post(url, data=stats, headers=headers) as resp:
            self.bot.logger.info(f'DBots statistics returned {resp.status} for {stats}')

    async def on_guild_join(self, guild):
        await self.update()

    async def on_guild_remove(self, guild):
        await self.update()

    async def on_ready(self):
        await self.update()

    async def on_resume(self):
        await self.update()


def setup(bot: DiscordBot):
    bot.add_cog(Stats(bot))
