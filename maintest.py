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
        user_class TEXT NOT NULL CHECK (class IN ('sotr', 'ok'))
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


def get_user(chat_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"id": user[0], "username": user[1], "password": user[2], "full_name": user[3], "chat_id": user[4],
                "user_class": user[5]}
    else:
        return None


def get_users_by_class(user_class):
    # Запрос на получение пользователей с заданным классом из базы данных
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_class=?", (user_class,))
    rows = cursor.fetchall()
    conn.close()

    # Создаем список словарей с данными пользователей
    users = []
    for row in rows:
        user = {"id": row[0], "full_name": row[1], "user_class": row[3]}
        users.append(user)

    return users

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
    btn4 = types.KeyboardButton("Запрос")
    markup.add(btn1, btn2, btn3, btn4)

    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Запрос")
def handle_query(message):
    chat_id = message.chat.id
    user = get_user(chat_id)
    print(f"user: {user}")
    if user is not None and has_access_to_query(user):
        # Обрабатываем запрос от сотрудника предприятия
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Получение расчетного листа")
        btn2 = types.KeyboardButton("Получение расчета больничного")
        markup.add(btn1, btn2)
        bot.send_message(chat_id, "Выберите функцию:", reply_markup=markup)
        bot.register_next_step_handler(message, handle_query_selection)
    else:
        # Обрабатываем запрос от сотрудника отдела кадров
        bot.send_message(chat_id, "Сотрудник отдела кадров, у вас нет доступа к функции запроса.")

def has_access_to_query(user):
    if user["user_class"] == "sotr":
        # Проверяем, есть ли у сотрудника предприятия доступ к функции запроса
        return user.get("has_access_to_query", False)
    elif user["user_class"] == "ok":
        # Сотрудники отдела кадров не имеют доступа к функции запроса
        return False
    else:
        # Если не удалось определить класс пользователя, то он не имеет доступа к функции запроса
        return False



def handle_query_selection(message):
    chat_id = message.chat.id
    user = get_user(chat_id)
    if has_access_to_query(user):
        if message.text == "Получение расчетного листа":
            function = "расчетный лист"
        elif message.text == "Получение расчета больничного":
            function = "расчет больничного"
        else:
            bot.send_message(chat_id, "Ошибка. Неизвестный выбор пользователя.")
            return
        # Отправляем запрос на получение расчета
        send_request(chat_id, user["full_name"], user["user_class"], function)
    else:
        bot.send_message(chat_id, "Сотрудник отдела кадров, у вас нет доступа к функции запроса.")


def send_request(message, full_name, user_class, function):
    chat_id = message.chat.id
    # Находим всех сотрудников отдела кадров
    ok_users = get_users_by_class("ok")
    if len(ok_users) == 0:
        bot.send_message(chat_id, "Ошибка. Нет сотрудников отдела кадров.")
        return
    # Находим сотрудников предприятия
    sotr_users = get_users_by_class("sotr")
    if len(sotr_users) == 0:
        bot.send_message(chat_id, "Ошибка. Нет зарегистрированных сотрудников предприятия.")
        return
    # Находим всех руководителей
    director_users = get_users_by_class("director")
    if len(director_users) == 0:
        bot.send_message(chat_id, "Ошибка. Нет зарегистрированных руководителей предприятия.")
        return
    # Проверяем класс пользователя
    if user_class == "sotr":
        # Отправляем запрос сотруднику отдела кадров
        request_text = f"Сотрудник {full_name} из класса {user_class} запрашивает {function}."
        for ok_user in ok_users:
            bot.send_message(ok_user["chat_id"], request_text)

        # Ждем ответа от сотрудника отдела кадров
        bot.send_message(chat_id, "Запрос отправлен. Ожидайте ответа от сотрудника отдела кадров.")
    elif user_class == "director":
        # Отправляем запрос всем руководителям
        request_text = f"Руководитель {full_name} из класса {user_class} запрашивает {function}."
        for director_user in director_users:
            bot.send_message(director_user["chat_id"], request_text)

        # Ждем ответа от руководителей
        bot.send_message(chat_id, "Запрос отправлен. Ожидайте ответа от руководителей.")
    else:
        bot.send_message(chat_id, "Ошибка. Недопустимый класс пользователя.")



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
    c.execute("SELECT full_name, user_class FROM users WHERE username=?", (username,))
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


# Запускаем бота
bot.polling(none_stop=True, interval=0)
# Закрываем соединение с базой данных
conn.close()
