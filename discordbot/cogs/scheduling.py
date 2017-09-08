import asyncio
import datetime
import json

import asyncqlio
import asyncqlio.exc
import discord

from discordbot.cogs.utils.tables import Schedule, Table
from discordbot.cogs.utils.util import validate_yourls


class Scheduling:
    """Reminders to do something."""

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.db.bind_tables(Table)
        self._have_data = asyncio.Event(loop=bot.loop)
        self._current_timer = None
        self._task = bot.loop.create_task(self.dispatch_timers())

    def __unload(self):
        self._task.cancel()

    async def get_active_timers(self, *, days=7):
        days = datetime.datetime.utcnow() + datetime.timedelta(days)
        async with self.bot.db.get_session() as s:
            query = await s.select(Schedule).where(Schedule.expires < days).order_by(Schedule.expires).all()
            query = await query.flatten()

            return query

    async def wait_for_active_timers(self, *, days=7):
        timers = await self.get_active_timers(days=days)
        if len(timers):
            self._have_data.set()
            return timers

        self._have_data.clear()
        self._current_timer = None
        await self._have_data.wait()
        return await self.get_active_timers(days=days)

    async def call_timer(self, timer):
        # delete the timer
        async with self.bot.db.get_session() as s:
            await s.remove(timer)

            # dispatch the event
            event_name = timer.event
            self.bot.dispatch(event_name, timer)

    async def dispatch_timers(self):
        try:
            while not self.bot.is_closed():
                # can only asyncio.sleep for up to ~48 days reliably
                # so we're gonna cap it off at 40 days
                # see: http://bugs.python.org/issue20493
                timers = await self.wait_for_active_timers(days=40)
                if timers:
                    timer = self._current_timer = timers[0]
                    now = datetime.datetime.utcnow()

                    if timer.expires >= now:
                        to_sleep = (timer.expires - now).total_seconds()
                        await asyncio.sleep(to_sleep)

                    await self.call_timer(timer)
        except asyncio.CancelledError:
            pass
        except (OSError, discord.ConnectionClosed, asyncqlio.exc.DatabaseException):
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_timers())

    async def short_timer_optimisation(self, seconds, timer):
        await asyncio.sleep(seconds)
        event_name = timer.event
        self.bot.dispatch(event_name, timer)

    async def create_timer(self, attrs: dict):
        """
        Creates a timer.
        """

        when = datetime.datetime.utcnow() + datetime.timedelta(seconds=attrs.pop("expires"))
        attrs["expires"] = when
        now = datetime.datetime.utcnow()
        delta = (when - now).total_seconds()
        timer = Schedule(**attrs)
        if delta <= 60:
            # a shortcut for small timers
            self.bot.loop.create_task(self.short_timer_optimisation(delta, timer))
            return timer

        async with self.bot.db.get_session() as s:
            await s.add(timer)

        self._have_data.set()

        # check if this timer is earlier than our currently run timer
        if self._current_timer and when < self._current_timer.expires:
            # cancel the task and re-run it
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_timers())

        return timer

    @staticmethod
    async def on_handle_delete(timer, seconds: int = None, url=None):
        """
        Deletes a short link.
        """
        yourl = validate_yourls()
        if not seconds and not url:
            url = json.loads(timer.extras)["url"]
            await yourl.delete(url)
        else:
            await asyncio.sleep(seconds)
            await yourl.delete(url)


def setup(bot):
    bot.add_cog(Scheduling(bot))
