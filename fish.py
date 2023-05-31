import requests
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
import os

from dotenv import load_dotenv

load_dotenv()

updater = Updater(token=os.getenv('TOKEN'))
URL_TASK = os.getenv('URL_TASK')
URL_CAT = os.getenv('URL_CAT')
URL_CREATE_USER = os.getenv("URL_CREATE_USER")
URL_CHECK_USER = os.getenv("URL_CHECK_USER")
URL_SCORE = os.getenv("URL_SCORE")
write_answer = None
try_number = None
task_id = None
button = ReplyKeyboardMarkup([['Математика', 'Рыбки', 'Покажи котика']], resize_keyboard=True)

def get_new_image():
    """Получение фото котика."""
    response = requests.get(URL_CAT).json()
    random_cat = response[0].get('url')
    return random_cat

def new_cat(update, context):
    """Отправка фото котика."""
    chat = update.effective_chat
    context.bot.send_photo(chat.id, get_new_image())


def new_task(update, context):
    """Получение новой задачи от API."""
    global write_answer, try_number, task_id
    chat = update.effective_chat
    response=requests.get(URL_TASK).json()
    context.bot.send_message(chat.id, text=response[0]['text'])
    task_id = response[0]['id']
# не удалять!!! кусок ждёт появления картинок на сервере!!!
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
        processing_score(try_number, chat.id)
        continue_work(update, context)
    else:
        try_number+=1
        if try_number < 4:
            context.bot.send_message(chat.id, text="Ответ неверный. Попробуй еще раз.")
            read_answer()
        else:
            context.bot.send_message(chat.id, text=f"Верный ответ: {write_answer}")
            processing_score(try_number, chat.id)
            continue_work(update, context)

def processing_score(try_number, chat_id):
    """Обработка рейтинговых очков."""
    response = requests.get(URL_CHECK_USER.format(id=chat_id)).json()
    id = response[0]['id']
    requests.patch(URL_SCORE.format(id=id), json={'score': 13-try_number*3, 'solved_tasks': [task_id]})


def fish(update, context):
    """Работа с рыбками."""
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id, text='Рыбок пока не подключили')

def wake_up(update, context):
    """Запуск бота."""
    chat = update.effective_chat
    name = update.message.chat.first_name
    response = requests.get(URL_CHECK_USER.format(id=chat.id)).json()
    if len(response) == 0:
        requests.post(URL_CREATE_USER, json={"player_id": chat.id})
        score = ''
    else:
        score = 'Твой текущий счет {}.'.format(response[0]['score'])  
    context.bot.send_message(
        chat_id=chat.id,
        text=f'Привет, {name}. {score} С чего начнём?',
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
#updater.dispatcher.add_handler(CommandHandler('Math', new_task))
updater.dispatcher.add_handler(MessageHandler(Filters.regex(r'Математика'), new_task))
updater.dispatcher.add_handler(MessageHandler(Filters.regex(r'Рыбки'), fish))
#updater.dispatcher.add_handler(CommandHandler('Fish', fish))
#updater.dispatcher.add_handler(CommandHandler('newcat', new_cat))
updater.dispatcher.add_handler(MessageHandler(Filters.regex(r'котика'), new_cat))

updater.start_polling()
updater.idle() 