# Импортируем нужные библиотеки
from collections import UserDict
from telebot import apihelper
from telebot import types
import telebot
import sqlite3

# Используем прокси
PROXY = 'whop1074:998899@45.145.232.50:61234'
apihelper.proxy = {'https': 'http://' + PROXY}
# Указываем токен бота
token = '5904272979:AAEPR8wJa4b-S9Tl1C_s1E_kz5rSpEBhRgs'
# Создаем экземпляр класса TeleBot
bot = telebot.TeleBot(token, parse_mode=None)

# Создаем соединение с базой данных
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Создаем таблицу users, если она не существует
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT,
        full_name TEXT,
        class TEXT NOT NULL CHECK (class IN ('sotr', 'ok'))
    )
''')

# Сохраняем изменения в базе данных
conn.commit()
# Закрываем соединение с базой данных
conn.close()

# Создаем экземпляр класса UserDict для хранения данных пользователей
user_data = UserDict()
# Создаем пустой словарь для хранения данных бота
bot_data = {}
# Создаем словарь для хранения данных пользователей
bot.user_data = {}


# Функция для проверки имени пользователя и пароля в БД
def check_credentials(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result is not None and (password is None or result[2] == password)


# Обработчик ввода имени пользователя
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id

    # Проверяем, авторизован ли пользователь
    if chat_id in bot.user_data:
        show_menu(chat_id)
        return

    # Сохраняем имя пользователя в глобальном словаре
    bot.user_data[chat_id] = {"username": None}

    def handle_username(message):
        chat_id = message.chat.id
        username = message.text

        # Проверяем, что имя пользователя введено верно
        if not check_credentials(username, None):
            bot.send_message(chat_id, "Неверное имя пользователя, попробуйте еще раз.")
            bot.register_next_step_handler(message, handle_username)
            return

        # Сохраняем имя пользователя в глобальном словаре
        bot.user_data[chat_id] = {"username": username}

        # Отправляем сообщение с запросом пароля
        bot.send_message(chat_id, "Введите пароль: ")
        bot.register_next_step_handler(message, handle_password)

    bot.send_message(chat_id, "Введите имя пользователя: ")
    bot.register_next_step_handler(message, handle_username)


# Обработчик ввода пароля пользователя
def handle_password(message):
    chat_id = message.chat.id
    password = message.text
    username = bot.user_data[chat_id]["username"]

    # Проверяем, что пароль введен верно
    if not check_credentials(username, password):
        bot.send_message(chat_id, "Неверный пароль, попробуйте еще раз.")
        bot.register_next_step_handler(message, handle_password)
        return

    # Сохраняем данные пользователя в словаре
    bot.user_data[chat_id]["password"] = password

    # Отправляем сообщение об успешной авторизации
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


# Обработчик кнопки "Профиль"
@bot.message_handler(func=lambda message: message.text == 'Профиль')
def handle_profile(message):
    chat_id = message.chat.id
    if chat_id not in bot.user_data:
        bot.send_message(chat_id, "Сначала авторизуйтесь, введя /start.")
        return
    username = bot.user_data[chat_id]["username"]
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT full_name, class FROM users WHERE username=?", (username,))
    full_name, user_class = c.fetchone()
    conn.close()
    if user_class == 'sotr':
        bot.send_message(chat_id, f"Вы - сотрудник предприятия\nВаше ФИО: \n{full_name}")
    elif user_class == 'ok':
        bot.send_message(chat_id, f"Вы - сотрудник отдела кадров\nВаше ФИО: \n{full_name}")


# Обработчик кнопки "Наши контакты"
@bot.message_handler(func=lambda message: message.text == 'Наши контакты 📞')
def handle_contacts(message):
    chat_id = message.chat.id
    if chat_id not in bot.user_data:
        bot.send_message(chat_id, "Сначала авторизуйтесь, введя /start.")
        return
    bot.send_message(message.chat.id,
                     "Номер телефона: +7 (863) 285-61-89\nАдрес: Степная ул., 16/1, Волгодонск\nНаш сайт: https://vpolesye.ru")


# Обработчик кнопки "Выход"
@bot.message_handler(func=lambda message: message.text == 'Выход 🔒')
def handle_exit(message):
    chat_id = message.chat.id
    # Удаляем данные пользователя из глобального словаря
    if chat_id in bot.user_data:
        del bot.user_data[chat_id]
    bot.send_message(chat_id, "Вы успешно вышли из аккаунта!\nДля того, чтобы войти, напишите /start")


@bot.message_handler(func=lambda message: message.text == 'Выход 🔒')
def logout(message):
    chat_id = message.chat.id
    # Удаляем данные пользователя из словаря
    if chat_id in bot_data:
        bot_data.pop(chat_id)

    # Удаляем данные пользователя из словаря bot.user_data
    if chat_id in bot.user_data:
        bot.user_data.pop(chat_id)

    # Выводим сообщение об успешном выходе
    logout_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    logout_markup.add(types.KeyboardButton('Авторизация ✅'))
    bot.send_message(chat_id, 'Вы успешно вышли! Для повторной авторизации введите имя пользователя:',
                     reply_markup=logout_markup)


@bot.message_handler(func=lambda message: message.text == 'Профиль')
def show_profile(message):
    chat_id = message.chat.id
    # Проверяем, авторизован ли пользователь
    if chat_id not in user_data:
        bot.send_message(chat_id, "Вы не авторизованы!")
        return

    # Отправляем сообщение с профилем пользователя
    username = user_data[chat_id]["username"]
    profile_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    profile_markup.add(types.KeyboardButton('Назад'))
    bot.send_message(chat_id, f"Профиль пользователя {username}", reply_markup=profile_markup)


# Запускаем бота
bot.polling(none_stop=True, interval=0)
# Закрываем соединение с базой данных
conn.close()
