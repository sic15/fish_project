import requests
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
import os

from dotenv import load_dotenv

load_dotenv()

updater = Updater(token=os.getenv('TOKEN'))
URL_TASK = os.getenv('URL_TASK')
write_answer = None
try_number = None

def new_task(update, context):
    """Получение новой задачи от API."""
    global write_answer, try_number
    chat = update.effective_chat
    response=requests.get(URL_TASK).json()
    context.bot.send_message(chat.id, text=response[0]['text'])
    write_answer = response[0]['answer']
    answer()
    try_number = 1

def answer():
    """Чтение ответа пользователя."""
    updater.dispatcher.add_handler(MessageHandler(Filters.text, check_answer))
    
def check_answer(update, context):
    """Обработка ответа пользователя."""
    global try_number
    chat = update.effective_chat
    if write_answer == update.message.text:
        context.bot.send_message(chat.id, text="Верный ответ!")
    else:
        try_number+=1
        if try_number < 4:
            context.bot.send_message(chat.id, text="Ответ неверный. Попробуй еще раз.")
            answer()
        else:
            context.bot.send_message(chat.id, text=f"Верный ответ: {write_answer}")

def fish(update, context):
    """Работа с рыбками."""
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id, text='Рыбок пока не подключили')

def wake_up(update, context):
    """Запуск бота."""
    chat = update.effective_chat
    name = update.message.chat.first_name
    button = ReplyKeyboardMarkup([['/Math', '/Fish']], resize_keyboard=True)

    context.bot.send_message(
        chat_id=chat.id,
        text='Привет, {}. С чего начнём?'.format(name),
        reply_markup=button
    )

updater.dispatcher.add_handler(CommandHandler('start', wake_up))
updater.dispatcher.add_handler(CommandHandler('Math', new_task))
updater.dispatcher.add_handler(CommandHandler('Fish', fish))

updater.start_polling()
updater.idle() 