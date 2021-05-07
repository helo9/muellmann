#!/usr/bin/env python
# pylint: disable=C0116
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to send timed Telegram messages.

This Bot uses the Updater class to handle the bot and the JobQueue to send
timed messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Alarm Bot example, sends a message after a set time.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import shelve
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, PicklePersistence

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


emojis = {
    'bio': ['\U0001F346', '\U0001F955', '\U0001F96C', '\U0001F966'],
    'rest': ['\U0001F961'],
    'papier': ['\U0001F4DC', '\U0001F4F0', '\U0001F3AB'],
    'plastik': ['\U00002678', '\U0001F36C']
}


trashtypes = "bio/rest/papier/plastik".split("/")
helptext = f"{{}} dd.mm.yyyy [{'/'.join(trashtypes)}]"
addhelptext = helptext.format('/add')
removehelptext = helptext.format('/remove')

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update: Update, _: CallbackContext) -> None:
    update.message.reply_text(f'Hi! Use \n{addhelptext}\n to add a trash date')


def alarm(context: CallbackContext) -> None:
    """Send the alarm message."""
    job = context.job
    
    trash_type = job.context["trash_type"]

    context.bot.send_message(job.context['chat_id'], 
                             text=f'\U0001F5D1\U0001F5D1\U0001F5D1*Tomorrow is trash date\!* \U0001F5D1\U0001F5D1\U0001F5D1\n\n_{trash_type}_: {"".join(emojis[trash_type])}', 
                             parse_mode="MarkdownV2")


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def build_job_id(chat_id, due, trash_type):
    return str(chat_id) + str(due) + str(trash_type)

def add(update: Update, context: CallbackContext) -> None:
    """Add another trash date to the queue."""

    if len(context.args) != 2:
        update.message.reply_text(f'Wrong input use {addhelptext}.')
        return

    chat_id = update.message.chat_id
    
    try:
        due = datetime.strptime(context.args[0], "%d.%m.%Y")
    except ValueError:
        update.message.reply_text(f'Given date was wrong, use {addhelptext}')
        return

    trash_type = str(context.args[1])
    
    if trash_type not in trashtypes:
        update.message.reply_text(f'Invalid trash type, use one of{",".join(trashtypes)}')
        return

    job_identifier = build_job_id(chat_id, due, trash_type)

    remove_job_if_exists(job_identifier, context)

    cbcontext = {
        'chat_id': chat_id,
        'trash_type': trash_type,
        'due': due
    }

    update.message.reply_text(f'Noted {trash_type} for {due}.')

    alarm_due = due - timedelta(days=1)

    context.job_queue.run_once(alarm, alarm_due, context=cbcontext, name=job_identifier)


def remove(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 2:
        update.message.reply_text(f'Wrong input use {removehelptext}.')
        return

    chat_id = update.message.chat_id
    
    try:
        due = datetime.strptime(context.args[0], "%d.%m.%Y")
    except ValueError:
        update.message.reply_text(f'Given date was wrong, use {removehelptext}')
        return

    trash_type = str(context.args[1])
    
    if trash_type not in trashtypes:
        update.message.reply_text(f'Invalid trash type, use one of{",".join(trashtypes)}')
        return

    job_id = build_job_id(chat_id, due, trash_type)

    if(remove_job_if_exists(job_id, context)):
        update.message.reply_text('Trash date succesfully removed.')
    else:
        update.message.reply_text('Could not remove trash date.')


def show_list(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id

    text = '*I have noted the following dates:*\n'

    for job in context.job_queue.jobs():
        duedate = job.context['due'].strftime("%d\.%m\.%Y")
        trash_type = job.context['trash_type']
        text += f'{duedate}  {trash_type}\n'

    update.message.reply_text(text, parse_mode="MarkdownV2")


def main() -> None:
    """Run bot."""
    
    # read Token from file
    with open('.TOKEN') as tokenfile:
        token = tokenfile.read(-1)
    
    # Create the Updater and pass it your bot's token.
    persistence = PicklePersistence(filename='müllstore.pkl')
    updater = Updater(token, persistence=persistence)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("add", add))
    dispatcher.add_handler(CommandHandler("help", start))
    dispatcher.add_handler(CommandHandler("remove", remove))
    dispatcher.add_handler(CommandHandler("list", show_list))

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
