import datetime

import pytz
from telegram.ext import ContextTypes

from db import Database


class DBJob:

    def __init__(self, database_file):
        self.__name__ = "DBJob"
        self.subscribers = []
        self.database_file = database_file

    def start(self, context: ContextTypes.DEFAULT_TYPE, chat_id):
        self.subscribe(chat_id)
        job_removed = self.remove_job_if_exists(str(chat_id), context)
        # context.job_queue.run_repeating(self.notify_bd, 5, name=str(chat_id))

        # notifying at 20 ETC about tomorrows birthday is optimal for both NA and Siberia
        # (hope it won't wake up our european friends :)
        context.job_queue.run_daily(self.notify_bd, datetime.time(hour=20, minute=0,
                                                                  tzinfo=pytz.timezone('US/Eastern')))

    def stop(self, context, chat_id):
        self.remove_job_if_exists(str(chat_id), context)

    @staticmethod
    def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if not current_jobs:
            return False
        for job in current_jobs:
            job.schedule_removal()
        return True

    def subscribe(self, subscriber_id):
        self.subscribers.append(subscriber_id)

    def unsubscribe(self, subscriber_id):
        self.subscribers.remove(subscriber_id)

    async def notify_bd(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        # Get today's and tomorrow's birthdays
        db = Database(self.database_file)
        people = db.get_upcoming_birthdays()
        message = "Thess people are having birthday very soon:\n"

        if len(people) > 0:
            # Construct a response with the names of the people whose birthday it is today or tomorrow
            for person in people:
                message += f"{person.full_name} on {person.birthday}\n\n"

        else:
            message = "nothing to see here.."

        # Send the response to all users
        for chat_id in self.subscribers:
            await context.bot.send_message(chat_id, text=message)
