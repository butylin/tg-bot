import datetime
import random

import pytz
from telegram.ext import ContextTypes

from db import Database

birthday_greetings = [
    "Поздравляем с днем рождения! Надеемся, ты не испугался своей тени.",
    "Сегодня твой день рождения! Не забудь выключить свои свечи, прежде чем пожарный департамент прибудет!",
    "С днем рождения! Желаем тебе, чтобы все твои подарки были полезными и не слишком уродливыми.",
    "Поздравляем тебя с днем рождения! Желаем тебе получить то, чего ты заслуживаешь, а не то, чего ты хочешь.",
    "С днем рождения! Желаем тебе, чтобы все твои мечты сбывались, кроме тех, которые могут повредить твоему здоровью.",
    "Поздравляем с днем рождения! Желаем тебе здоровья, счастья и много лет жизни. И не забудь, что ты стареешь!",
    "Сегодня твой день рождения! Желаем тебе много смеха, радости и любви. И не забудь, что взросление это ненавистное занятие!",
    "Поздравляем тебя с днем рождения! Желаем тебе найти счастье в жизни и в твоем банковском счете.",
    "С днем рождения! Желаем тебе получить все, что ты хочешь, кроме того, что ты уже имеешь.",
    "Поздравляем с днем рождения! Желаем тебе, чтобы все твои надежды стали реальностью, кроме тех, которые могут повредить твоей фигуре.",
    "С днем рождения! Желаем тебе много денег и бесконечного счастья. И не забудь, что деньги не могут купить тебе любовь, но они могут купить тебе пирожки!",
    "Поздравляем тебя с днем рождения! Желаем тебе, чтобы твоя жизнь была наполнена радостью, любовью и красивыми фотографиями на Instagram.",
    "С днем рождения! Желаем тебе найти свою половинку, но не забывай, что иногда две половинки могут быть лучше, чем целая.",
    "С днем рождения! Не старейте, а лучше молодейте!",
    "Поздравляю с днем рождения! Желаю радости, счастья и любви!",
    "Сегодня в твой день рождения желаю исполнения всех мечт и желаний!",
    "С днем рождения! Желаю больших успехов в работе и личной жизни!",
    "Поздравляю с днем рождения! Пусть всегда сопутствует удача и благополучие!",
    "С днем рождения! Желаю здоровья, счастья, исполнения желаний и мирного неба над головой!",
    "Поздравляю с днем рождения! Пусть жизнь будет яркой, насыщенной и полной счастья!",
    "С днем рождения! Пусть сбываются самые смелые мечты и желания!",
    "Поздравляю с днем рождения! Желаю счастья, удачи и всего самого наилучшего!",
    "С днем рождения! Пусть жизнь будет наполнена радостью, любовью и душевным теплом!"]


class DBJob:

    def __init__(self, database_file):
        self.__name__ = "DBJob"
        self.subscribers = set()
        self.database_file = database_file

    def start(self, context: ContextTypes.DEFAULT_TYPE, chat_id):
        self.subscribe(chat_id)
        job_removed = self.remove_job_if_exists(str(chat_id), context)
        # context.job_queue.run_repeating(self.notify_bd, 5, name=str(chat_id))

        # notifying at 20 ETC about tomorrows birthday is optimal for both NA and Siberia
        # (hope it won't wake up our european friends :)
        context.job_queue.run_daily(self.notify_bd,
                                    datetime.time(hour=9, minute=00, tzinfo=pytz.timezone('US/Eastern')),
                                    name=str(chat_id))

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
        self.subscribers.add(subscriber_id)

    def unsubscribe(self, subscriber_id):
        self.subscribers.remove(subscriber_id)

    async def notify_bd(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        # Get today's and tomorrow's birthdays
        db = Database(self.database_file)
        people = db.get_upcoming_birthdays()
        message = "Завтра ДР у:\n"

        if len(people) > 0:
            # Construct a response with the names of the people whose birthday it is today or tomorrow
            for person in people:
                message += f"{person.full_name} on {person.birthday}\n"
            message += "\n" + random.choice(birthday_greetings)

            # Send the response to all users
            for chat_id in self.subscribers:
                await context.bot.send_message(chat_id, text=message)
