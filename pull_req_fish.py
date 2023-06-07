import requests
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
import os

from dotenv import load_dotenv

load_dotenv()

updater = Updater(token=os.getenv('TOKEN'))
URL_CAT = os.getenv('URL_CAT')
URL = os.getenv('BKND_URL')
button = ReplyKeyboardMarkup(
    [['Математика', 'Рыбки', 'Покажи котика', 'Покажи мои баллы']], resize_keyboard=True)


class PlayerSession():
    def __init__(self, update, context):
        self.name = update.message.chat.first_name
        self.chat = update.effective_chat
        self.player_id = self.chat.id # telegram chat ID
        self.player_backend_id = self.get_or_create_player()
        self.current_score = self.get_user_score()

    def get_or_create_player(self):
        search_response = requests.get(f'{URL}/player/?player_id={self.player_id}').json()
        if len(search_response) == 0: # if not search_response
            response = requests.post(f'{URL}/player/', json={"player_id": self.player_id})
            return response.json().get('id')
        return search_response[0].get('id')

    def get_user_score(self):
        response:dict = requests.get(f'{URL}/player/{self.player_backend_id}/').json()
        return response.get('score')

    # def destruct_current_task(self): # Проба пера
    #     self.current_task.delete()


def get_new_image():
    """Получение фото котика."""
    response = requests.get(URL_CAT).json()
    random_cat = response[0].get('url')
    return random_cat

def new_cat(update, context):
    """Отправка фото котика."""
    chat = update.effective_chat
    context.bot.send_photo(chat.id, get_new_image())

def math(update, context):
    """Задачи по математике"""
    category = 1
    new_task(update, context, category)

def fish(update, context):
    """Работа с рыбками."""
    category = 2
    new_task(update, context, category)

def new_task(update, context, category):
    """Получение новой задачи от API."""
    global player_session
    current_task = requests.get(f'{URL}/randomtask/?category={category}&player_id={player_session.player_id}').json()
    if current_task:
        player_session.current_task = current_task[0]
        player_session.try_number = 1
        if player_session.current_task.get('text'):
            context.bot.send_message(player_session.player_id, text=player_session.current_task.get('text'))
        if player_session.current_task.get('image'):
            context.bot.send_photo(player_session.player_id, player_session.current_task.get('image'))
        updater.dispatcher.add_handler(MessageHandler(Filters.text, check_answer))
    else: # обработать блок
        player_session.current_task = {'category': category} # пишем категорию при пустой задаче
        button = ReplyKeyboardMarkup([['Да', 'Нет']], resize_keyboard=True)
        context.bot.send_message(player_session.player_id, text="Вы решили все задачи! Хотите начать сначала?", reply_markup=button)
        updater.dispatcher.add_handler(MessageHandler(Filters.regex(r'Да'), clean_category))
        updater.dispatcher.add_handler(MessageHandler(Filters.regex(r'Нет'), continue_work)) # wtf ? 
        updater.dispatcher.add_handler(
    MessageHandler(
        Filters.regex(r'баллы'),
        current_score))

def current_score(update, context):
    """Проверка текущего счета."""
    score = player_session.get_user_score()
    context.bot.send_message(player_session.player_id, text=f"Ваш текущий счет {score}")

def clean_category(update, context):
    """Очистка решенных задач пользователя по категории."""
    global player_session
    requests.delete(f'{URL}/player/{player_session.player_backend_id}/?category={player_session.current_task["category"]}')
    continue_work(update, context)


def check_answer(update, context):
    """Обработка ответа пользователя."""
    if update.message.text.lower() == player_session.current_task.get('answer').lower():
        context.bot.send_message(player_session.player_id, text="Верный ответ!")
        processing_score(context) #
    else:
        player_session.try_number += 1
        if player_session.try_number < 4:
            context.bot.send_message(
                player_session.player_id, text="Ответ неверный. Попробуй еще раз.")
            updater.dispatcher.add_handler(MessageHandler(Filters.text, check_answer))
        else: # 
            context.bot.send_message(
                player_session.player_id, text=f"Верный ответ: {player_session.current_task['answer']}")
            processing_score(context)
    context.bot.send_message(
        player_session.player_id,
        text='Что дальше?',
        reply_markup=button
    )


def processing_score(context):
    """Обработка рейтинговых очков."""
    task_score = 13 - player_session.try_number * 3
    requests.patch(f'{URL}/player/{player_session.player_backend_id}/',
                   json={
                    "score": task_score,
                    "solved_tasks": [player_session.current_task['id']]
                   })
    context.bot.send_message(player_session.player_id, text=f'Баллы за эту задачу: {task_score}')

def wake_up(update, context):
    """Запуск бота."""
    global player_session
    player_session = PlayerSession(update, context)
    continue_work(update, context)

def continue_work(update, context):
    score_message = f'Твой текущий счет: {player_session.get_user_score()}.'
    context.bot.send_message(
        chat_id=player_session.player_id,
        text=f'Привет, {player_session.name}. {score_message} С чего начнём?',
        reply_markup=button
    )

updater.dispatcher.add_handler(CommandHandler('start', wake_up))
updater.dispatcher.add_handler(
    MessageHandler(
        Filters.regex(r'Матем'),
        math))
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
