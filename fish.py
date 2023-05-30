import requests
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
import os

from dotenv import load_dotenv

load_dotenv()

updater = Updater(token=os.getenv('TOKEN'))
URL_TASK = os.getenv('URL_TASK')
URL_CAT = os.getenv('URL_CAT')
write_answer = None
try_number = None
button = ReplyKeyboardMarkup([['/Math', '/Fish', '/newcat']], resize_keyboard=True)

def get_new_image():
    """Получение фото котика."""
    response = requests.get(URL_CAT).json()
    random_cat = response[0].get('url')
    return random_cat

def new_cat(update, context):
    """Отправка фото котика."""
    chat = update.effective_chat
    context.bot.send_photo(chat.id, get_new_image())
 #   context.bot.send_photo(chat.id, 'http://mysite.xyz:8000/media/quizzles/photo_2020-03-26_16-38-14.jpg')



def new_task(update, context):
    """Получение новой задачи от API."""
    global write_answer, try_number
    chat = update.effective_chat
    response=requests.get(URL_TASK).json()
    context.bot.send_message(chat.id, text=response[0]['text'])
#    if response[0]['image']:
#        context.bot.send_photo(chat.id, response[0]['image'])
    write_answer = response[0]['answer']
    read_answer()
    try_number = 1

def read_answer():
    """Чтение ответа пользователя."""
    updater.dispatcher.add_handler(MessageHandler(Filters.text, check_answer))
    
def check_answer(update, context):
    """Обработка ответа пользователя."""
    global try_number
    chat = update.effective_chat
    if write_answer.lower() == update.message.text.lower():
        context.bot.send_message(chat.id, text="Верный ответ!")
        continue_work(update, context)
    else:
        try_number+=1
        if try_number < 4:
            context.bot.send_message(chat.id, text="Ответ неверный. Попробуй еще раз.")
            read_answer()
        else:
            context.bot.send_message(chat.id, text=f"Верный ответ: {write_answer}")
            continue_work(update, context)

def fish(update, context):
    """Работа с рыбками."""
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id, text='Рыбок пока не подключили')

def wake_up(update, context):
    """Запуск бота."""
    chat = update.effective_chat
    name = update.message.chat.first_name
    
    context.bot.send_message(
        chat_id=chat.id,
        text='Привет, {}. С чего начнём?'.format(name),
        reply_markup=button
    )

def continue_work(update, context):
    """Продолжение работы."""
    chat = update.effective_chat
    name = update.message.chat.first_name
    context.bot.send_message(
        chat_id=chat.id,
        text='Что дальше?'.format(name),
        reply_markup=button
    )

updater.dispatcher.add_handler(CommandHandler('start', wake_up))
updater.dispatcher.add_handler(CommandHandler('Math', new_task))
#updater.dispatcher.add_handler(MessageHandler(MessageHandler.filters.Regex('Math'), new_task))
updater.dispatcher.add_handler(CommandHandler('Fish', fish))
updater.dispatcher.add_handler(CommandHandler('newcat', new_cat))

updater.start_polling()
updater.idle() 