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
URL_CONTROL_USER = os.getenv("URL_CONTROL_USER")
URL = os.getenv('BKND_URL')
write_answer = None
try_number = None
task_id = None
button = ReplyKeyboardMarkup(
    [['Математика', 'Рыбки', 'Покажи котика', 'Покажи мои баллы']], resize_keyboard=True)


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
    response = requests.get(URL_TASK.format(chat_id=chat.id)).json()
    if len(response) > 0:
        context.bot.send_message(chat.id, text=response[0]['text'])
        task_id = response[0]['id']
        # не удалять!!! кусок ждёт появления картинок на сервере!!!
        if response[0]['image']:
            context.bot.send_photo(chat.id, response[0]['image'])
        write_answer = response[0]['answer']
        read_answer()
        try_number = 1
    else:
        button = ReplyKeyboardMarkup([['Да', 'Нет']], resize_keyboard=True)
        context.bot.send_message(chat.id, text="Вы решили все задачи! Хотите начать сначала?", reply_markup=button)
        updater.dispatcher.add_handler(MessageHandler(Filters.regex(r'Да'), del_user))
        updater.dispatcher.add_handler(MessageHandler(Filters.regex(r'Нет'), continue_work))
        updater.dispatcher.add_handler(
    MessageHandler(
        Filters.regex(r'баллы'),
        current_score))

def current_score(update, context):
    """Проверка текущего счета."""
    chat = update.effective_chat
    response = requests.get(URL_CHECK_USER.format(id=chat.id)).json()
    id = response[0]['id']
    response = requests.get(URL_CONTROL_USER.format(id=id)).json()
   # print(response)
    context.bot.send_message(chat.id, text=f"Ваш текущий счет {response['score']}")

def del_user(update, context):
    """Удаление пользователя."""
    chat = update.effective_chat
    response = requests.get(URL_CHECK_USER.format(id=chat.id)).json()
    id = response[0]['id']
    requests.delete(URL_CONTROL_USER.format(id=id))
    wake_up(update, context)

def read_answer():
    """Чтение ответа пользователя."""
    updater.dispatcher.add_handler(MessageHandler(Filters.text, check_answer))


def check_answer(update, context):
    """Обработка ответа пользователя."""
    global try_number
    chat = update.effective_chat
    if write_answer.lower() == update.message.text.lower():
        context.bot.send_message(chat.id, text="Верный ответ!")
        processing_score(context, try_number, chat.id)
        continue_work(update, context)
    else:
        try_number += 1
        if try_number < 4:
            context.bot.send_message(
                chat.id, text="Ответ неверный. Попробуй еще раз.")
            read_answer()
        else:
            context.bot.send_message(
                chat.id, text=f"Верный ответ: {write_answer}")
            processing_score(context, try_number, chat.id)
            continue_work(update, context)


def processing_score(context, try_number, chat_id):
    """Обработка рейтинговых очков."""
    response = requests.get(URL_CHECK_USER.format(id=chat_id)).json()
    if len(response) > 0:
        id = response[0]['id']
        score = 13 - try_number * 3
        requests.patch(URL_CONTROL_USER.format(id=id),
            json={
                "score": score,
                "solved_tasks": [task_id]})
        context.bot.send_message(chat_id=chat_id, text=f'Баллы за эту задачу: {score}')


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
updater.dispatcher.add_handler(
    MessageHandler(
        Filters.regex(r'Матем'),
        new_task))
updater.dispatcher.add_handler(MessageHandler(Filters.regex(r'Рыб'), fish))
updater.dispatcher.add_handler(
    MessageHandler(
        Filters.regex(r'кот'),
        new_cat))
updater.dispatcher.add_handler(
    MessageHandler(
        Filters.regex(r'баллы'),
        current_score))

updater.start_polling()
updater.idle()
