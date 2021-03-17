import asyncio
import time
import datetime
import uuid
from typing import TYPE_CHECKING

import pytz as pytz

if TYPE_CHECKING:
    from core import Core


UTC = pytz.UTC


class Timer:

    def __init__(self, core: 'Core', tz=UTC):
        self._tasks = {}
        self._id_counter = 0
        self.time_zone = tz
        self.core: 'Core' = core

    def scheduled_call(self, cb, delay=None, target_time: datetime.datetime = None):
        """
        schedules a task to be executed at a certain time point or after a certain delay
        :param cb: task
        :param delay: delay
        :param target_time: time point
        :return: handler (task)
        """
        now = datetime.datetime.now(self.time_zone)
        if delay is not None:
            slp_seconds = delay - (now.microsecond / 10 ** 6)
        else:
            slp_seconds = (target_time - now).total_seconds()
        target = time.monotonic() + slp_seconds

        return self.core.event_loop.call_later(
            slp_seconds, lambda: self.core.add_job(cb, target)
        )
    
    def daily(self, cb, run_time: datetime.datetime):
        """
        schedules a task to be called on a daily base.
        :param cb: callback
        :param run_time: datetime
        :return: handler
        """

        class job:
            def __init__(j, run_time):
                j.run_time = run_time
                j.task = None

            def run(j):
                j.run_time = j.run_time + datetime.timedelta(days=1)
                self.core.add_job(cb)
                j.task = self.scheduled_call(j.run, target_time=j.run_time)

            def cancel(j):
                j.task.cancel()

        j = job(run_time)
        j.task = self.scheduled_call(j.run, target_time=run_time)
        return j.cancel

    def periodic_job(
        self, interval, callback, wait_for_job=True, event: asyncio.Event = None
    ) -> asyncio.Task:
        """
        schedules a task to be executed in a regular interval
        :param interval: call interval
        :param callback: task to execute
        :param wait_for_job: should the scheduler wait until the task has finished before rescheduling it
        :param event: asyncio event to block the execution
        :return: handler
        """

        task_id = uuid.uuid4()

        async def cb(t):
            if event:
                await event.wait()
            if wait_for_job:
                await self.core.async_add_job(callback)
            else:
                self.core.add_job(callback)
            self._tasks[task_id] = self.scheduled_call(
                lambda x: self.core.add_job(cb, x), interval
            )

        self._tasks[task_id] = self.scheduled_call(
            lambda x: self.core.add_job(cb, x), delay=1
        )

        def stop():
            self._tasks[task_id].cancel()

        return stop
