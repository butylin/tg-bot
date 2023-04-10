import json
import logging
import re
from datetime import datetime
import shutil

import telegram
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, Application, filters, CommandHandler, MessageHandler

from bday_job import DBJob
from db import Database
from person import Person

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {telegram.__version__}. To view the "
        f"{telegram.__version__} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{telegram.__version__}/examples.html"
    )

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('../logs/bot.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logging.getLogger().addHandler(logging.NullHandler())
logging.getLogger().propagate = True

# Set up a logger for the apscheduler library
scheduler_logger = logging.getLogger('apscheduler')
scheduler_logger.addHandler(file_handler)
scheduler_logger.setLevel(logging.INFO)

# Set up a logger for the telegram.ext library
telegram_logger = logging.getLogger('telegram')
telegram_logger.addHandler(file_handler)
telegram_logger.setLevel(logging.INFO)

DATBASE_FILE: str = "../db/people.db"
CONFIG_FILE: str = "../config/bot.conf"
CONFIRM_DELETE = 0

bday_job = DBJob(DATBASE_FILE)


def get_command_agrs(update) -> str:
    full_str = update.message.text
    try:
        command, msg = full_str.split(maxsplit=1)
        return msg
    except ValueError as e:
        return ""


def split_name_and_date(input_str):
    # define a regular expression pattern to match a date in the format dd-mm-YYYY
    date_pattern = r'\d{1,2}-\d{1,2}-\d{4}'
    match = re.search(date_pattern, input_str)

    if match:
        date_str = match.group()
        input_str = input_str.replace(date_str, '')
    else:
        date_str = None

    input_str = input_str.strip()
    return input_str, date_str


def days_until_birthday(person):
    today = datetime.today().date()
    date = datetime.strptime(person.birthday, '%Y-%m-%d').date()
    birthday = date.replace(year=today.year)
    if birthday < today:
        # This person's birthday has already passed this year, so use next year's birthday instead.
        birthday = birthday.replace(year=today.year + 1)
    return (birthday - today).days


def read_config():
    with open('../config/bot.conf', 'r') as f:
        config = json.load(f)

    token = config['token']
    allowed_users = config['users']
    allowed_chats = config['chats']

    return token, allowed_users, allowed_chats


# handles /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    bday_job.start(context, chat_id)
    await context.bot.sendMessage(chat_id, "starting bday notificator..")


# handles /start command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    bday_job.stop(context, chat_id)
    await context.bot.sendMessage(chat_id, "bday notificator stopped..")


async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response_id = update.message.chat_id
    backup_filepath = DATBASE_FILE + ".bak"
    shutil.copy2(DATBASE_FILE, backup_filepath)
    await context.bot.sendMessage(response_id, f"Created backup copy of {DATBASE_FILE} at {backup_filepath}")


# handles /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = "Доступные команды:\n"
    help_text += "/list - список всех людей с датами их рождения\n"
    help_text += "/next - следующий именинник\n"
    help_text += "/add name date - добавляет нового человека с указанным именем и датой рождения\n"
    help_text += "/del index - удаляет человека с указанным номером из списка\n"
    # help_text = "Available commands:\n"
    # help_text += "/help - shows the help message\n"
    # help_text += "/list - lists all the people with their birthdays\n"
    # help_text += "/add name date - adds a new person with the given fu name and birthday\n"
    # help_text += "/del index - deletes the person with the given index\n"

    await update.message.reply_text(help_text)


# handles /list command
async def bday_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sorted_people = get_bday_sorted_by_nearest()

    if len(sorted_people) < 1:
        await update.message.reply_text("Список пуст")

    bdays_str = ""
    for person in sorted_people:
        bdays_str += f"#{person.id}: {person.full_name} - {datetime.strptime(person.birthday, '%Y-%m-%d').date().strftime('%d-%m-%Y')}\n"

    await update.message.reply_text(bdays_str)


# handles /next command
async def bday_next_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sorted_people = get_bday_sorted_by_nearest()

    if len(sorted_people) > 0:
        nextbd = sorted_people[0]
        await update.message.reply_text(f"Следующий именинник: {nextbd.full_name} - {nextbd.birthday}")


def get_bday_sorted_by_nearest() -> list[Person]:
    db = Database(DATBASE_FILE)

    people = db.get_people()
    if len(people) > 0:
        return sorted(people, key=days_until_birthday)
    else:
        return []


# handles /add command
async def bday_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = get_command_agrs(update)

    if len(message) < 1:
        await update.message.reply_text("Пропущен обязательный параметр")

    name, bday = split_name_and_date(message)

    db = Database(DATBASE_FILE)
    db.insert_person(name, bday)

    reply = f"ДР для {name} теперь {bday}!"
    logger.info(reply)
    await update.message.reply_text(reply)


# handles /del command
async def bday_del_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO: only allow deletion for admins or whoever added the birthday
    index_to_delete = get_command_agrs(update)
    if len(index_to_delete) < 1:
        await update.message.reply_text("Пропущен обязательный параметр")
        return ConversationHandler.END

    person_to_delete = Database(DATBASE_FILE).get_person(index_to_delete)
    if person_to_delete is None:
        await update.message.reply_text(f"Не найдено людей с #{index_to_delete}")
        return ConversationHandler.END

    context.user_data["index_to_delete"] = person_to_delete.id
    reply_keyboard = [['Да', 'Нет']]
    await update.message.reply_text(
        f"Точно хотите удалить {person_to_delete.full_name}?",
        reply_markup=telegram.ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )

    return CONFIRM_DELETE


# handles response to bday_del_command
async def handle_confirmation_response(update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    if str(response).lower() in ['да', 'yes']:
        index_to_delete = context.user_data["index_to_delete"]
        db = Database(DATBASE_FILE)
        db.delete_person(index_to_delete)
        await update.message.reply_text('Удаление успешно.', reply_markup=telegram.ReplyKeyboardRemove())
    else:
        await update.message.reply_text('Удаление отменено.', reply_markup=telegram.ReplyKeyboardRemove())

    # End the conversation
    return ConversationHandler.END


async def error_handler(update, context):
    logger.error(f"Exception while handling an update: {context.error}")
    await update.message.reply_text(f"Exception while handling an update: {context.error}")


def main() -> None:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    admin = config['admin']
    token = config['token']
    allowed_users = config['users']
    allowed_chats = config['chats']

    application = Application.builder().token(token).build()
    access_filter = filters.User(allowed_users) | filters.Chat(allowed_chats)

    # define admin commands
    application.add_handler(CommandHandler("start", start, filters.User(admin)))
    application.add_handler(CommandHandler("stop", stop, filters.User(admin)))
    application.add_handler(CommandHandler("backup", backup, filters.User(admin)))

    # define user commands
    application.add_handler(CommandHandler("help", help_command, access_filter))
    application.add_handler(CommandHandler("list", bday_list_command, access_filter))
    application.add_handler(CommandHandler("add", bday_add_command, access_filter))
    application.add_handler(CommandHandler("next", bday_next_command, access_filter))

    # used for the confirmation dialog during deletion
    bday_deletion_handler = ConversationHandler(
        entry_points=[CommandHandler("del", bday_del_command, access_filter)],
        states={
            CONFIRM_DELETE: [MessageHandler(filters.TEXT, handle_confirmation_response)],
        },
        fallbacks=[],
        allow_reentry=True
    )
    application.add_handler(bday_deletion_handler)
    
    # application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
