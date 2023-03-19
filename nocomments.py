from collections import UserDict
from telebot import apihelper
from telebot import types
import telebot
import sqlite3

PROXY = 'whop1074:998899@45.145.232.50:61234'
apihelper.proxy = {'https': 'http://' + PROXY}

token = '5904272979:AAEPR8wJa4b-S9Tl1C_s1E_kz5rSpEBhRgs'

bot = telebot.TeleBot(token, parse_mode=None)

conn = sqlite3.connect('users.db')
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT,
        full_name TEXT,
        class TEXT NOT NULL CHECK (class IN ('sotr', 'ok'))
    )
''')

conn.commit()

conn.close()

user_data = UserDict()

bot_data = {}

bot.user_data = {}


def check_credentials(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result is not None and (password is None or result[2] == password)


@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id

    if chat_id in bot.user_data:
        show_menu(chat_id)
        return

    bot.user_data[chat_id] = {"username": None}

    def handle_username(message):
        chat_id = message.chat.id
        username = message.text

        # Проверяем, что имя пользователя введено верно
        if not check_credentials(username, None):
            bot.send_message(chat_id, "Неверное имя пользователя, попробуйте еще раз.")
            bot.register_next_step_handler(message, handle_username)
            return

        bot.user_data[chat_id] = {"username": username}

        bot.send_message(chat_id, "Введите пароль: ")
        bot.register_next_step_handler(message, handle_password)

    bot.send_message(chat_id, "Введите имя пользователя: ")
    bot.register_next_step_handler(message, handle_username)


def handle_password(message):
    chat_id = message.chat.id
    password = message.text
    username = bot.user_data[chat_id]["username"]

    # Проверяем, что пароль введен верно
    if not check_credentials(username, password):
        bot.send_message(chat_id, "Неверный пароль, попробуйте еще раз.")
        bot.register_next_step_handler(message, handle_password)
        return

    bot.user_data[chat_id]["password"] = password

    bot.send_message(chat_id, "Авторизация прошла успешно!")
    show_menu(chat_id)


def show_menu(chat_id):
    if chat_id not in bot.user_data:
        bot.send_message(chat_id, "Сначала авторизуйтесь, введя /start.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Профиль")
    btn2 = types.KeyboardButton("Наши контакты 📞")
    btn3 = types.KeyboardButton("Выход 🔒")
    markup.add(btn1, btn2, btn3)
    bot.send_message(chat_id, 'Выберите действие:', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Профиль')
def handle_profile(message):
    chat_id = message.chat.id
    if chat_id not in bot.user_data:
        bot.send_message(chat_id, "Сначала авторизуйтесь, введя /start.")
        return
    username = bot.user_data[chat_id]["username"]
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT full_name FROM users WHERE username=?", (username,))
    full_name = c.fetchone()[0]
    conn.close()
    bot.send_message(chat_id, f"Ваше ФИО: \n{full_name}")


@bot.message_handler(func=lambda message: message.text == 'Наши контакты 📞')
def handle_contacts(message):
    chat_id = message.chat.id
    if chat_id not in bot.user_data:
        bot.send_message(chat_id, "Сначала авторизуйтесь, введя /start.")
        return
    bot.send_message(message.chat.id,
                     "Номер телефона: +7 (863) 285-61-89\nАдрес: Степная ул., 16/1, Волгодонск\nНаш сайт: https://vpolesye.ru")


@bot.message_handler(func=lambda message: message.text == 'Выход 🔒')
def handle_exit(message):
    chat_id = message.chat.id

    if chat_id in bot.user_data:
        del bot.user_data[chat_id]
    bot.send_message(chat_id, "Вы успешно вышли из аккаунта!\nДля того, чтобы войти, напишите /start")


@bot.message_handler(func=lambda message: message.text == 'Выход 🔒')
def logout(message):
    chat_id = message.chat.id

    if chat_id in bot_data:
        bot_data.pop(chat_id)

    if chat_id in bot.user_data:
        bot.user_data.pop(chat_id)

    logout_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    logout_markup.add(types.KeyboardButton('Авторизация ✅'))
    bot.send_message(chat_id, 'Вы успешно вышли! Для повторной авторизации введите имя пользователя:',
                     reply_markup=logout_markup)


@bot.message_handler(func=lambda message: message.text == 'Профиль')
def show_profile(message):
    chat_id = message.chat.id

    if chat_id not in user_data:
        bot.send_message(chat_id, "Вы не авторизованы!")
        return

    username = user_data[chat_id]["username"]
    profile_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    profile_markup.add(types.KeyboardButton('Назад'))
    bot.send_message(chat_id, f"Профиль пользователя {username}", reply_markup=profile_markup)


bot.polling(none_stop=True, interval=0)
conn.close()
