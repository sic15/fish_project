import requests
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
import os

from dotenv import load_dotenv

load_dotenv()

updater = Updater(token=os.getenv('TOKEN'))
URL = 'https://api.thecatapi.com/v1/images/search'

def get_new_task():
    response = requests.get(URL).json()
    random_cat = response[0].get('url')
    return random_cat

def new_task(update, context):
    chat = update.effective_chat
    context.bot.send_message(chat.id, text=get_new_task())
    updater.dispatcher.add_handler(MessageHandler(Filters.text, check_answer))

def check_answer(update, context):
    chat = update.effective_chat
    print(update.message.text)



def fish(update, context):
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id, text='Рыбок пока не подключили')

def wake_up(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    button = ReplyKeyboardMarkup([['/Math', '/Fish']], resize_keyboard=True)

    context.bot.send_message(
        chat_id=chat.id,
        text='Привет, {}. С чего начнём?'.format(name),
        reply_markup=button
    )

  #  context.bot.send_photo(chat.id, get_new_image())

updater.dispatcher.add_handler(CommandHandler('start', wake_up))
updater.dispatcher.add_handler(CommandHandler('Math', new_task))
updater.dispatcher.add_handler(CommandHandler('Fish', fish))

updater.start_polling()
updater.idle() 