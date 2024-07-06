import telebot
from telebot import types
import requests
import bd

print("I am working")

token = '5991335757:AAEpo4aN9J_5ix182qQ767NqLubVlwe2WME'
bot = telebot.TeleBot(token)
data_in = {"name_in": "",
           "area_in": [],  # {"id":,"text":""}
           "schedule": [{"id": "fullDay", "text": "Полный день", "state": False},
                        {"id": "shift", "text": "Сменный график", "state": False},
                        {"id": "flexible", "text": "Гибкий график", "state": False},
                        {"id": "remote", "text": "Удалённая работа", "state": False},
                        {"id": "flyInFlyOut", "text": "Вахтовый метод", "state": False}],
           "salary_in": "",
           "company_in": "",
           "show": 20,
           "show_url": False,
           "is_filtr_mode": False
           }
conn = bd.create_connection()
cursor = conn.cursor()
bd.drop_table(conn, cursor)
bd.create_table(conn, cursor)


def arr_str_to_str(arr):
    out = ""
    if arr:
        out += "'"
        out += "', '".join(arr)
        out += "'"
    return out


@bot.message_handler(commands=['start'])
def start(message):
    global data_in
    data_in["is_filtr_mode"] = False
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row("/start", "/help", "/Найти_вакансии", "/Фильтр_вакансий", "/Параметры")
    bot.send_message(message.chat.id, 'Вас приветствует "Менеджер вакансий". Этот бот разработан начинающим '
                                      'специалистом с целью удобного поиска и фильтрации вакансий с hh.ru.',
                     reply_markup=keyboard)


@bot.message_handler(commands=['help'])
def help_message(message):
    text = """
    В боте всего 3 раздела: стартовый, поиска и фильтрации
    Чтобы найти вакансии - переходим в раздел поиска - /Найти_вакансии
    Чтобы отобрать среди найденных вакансий нужные - в раздел фильтрации - /Фильтр_вакансий
    Чтобы посмотреть заданные параметры - /Параметры
    Чтобы сбросить параметры поиска/фильтрации - Сброс_параметров    
    """
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["Найти_вакансии"])
def find_menu(message):
    global data_in
    data_in["is_filtr_mode"] = False
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row("/Найти", "/start", "/help", "/Фильтр_вакансий", "/Параметры")
    keyboard.row("/Добавить_должность", "/Настроить_города")
    keyboard.row("/Настроить_график", "/Настроить_зарплату", "/Сброс_параметров")
    bot.send_message(message.chat.id, 'Настройте параметры поиска вакансий и нажмите на кнопку "Найти"',
                     reply_markup=keyboard)


@bot.message_handler(commands=["Добавить_должность"])
def name(message):
    bot.send_message(message.chat.id, 'Ниже напишите слово/словосочетание, которое должно быть в названии вакансии')
    bot.register_next_step_handler(message, get_name)


def get_name(message):
    global data_in
    str_mes = str(message.text).strip()
    if data_in["is_filtr_mode"]:
        data_in["name_in"] = str_mes.lower()
        bot.send_message(message.from_user.id, str('Фильтр по названию: ' + str_mes.lower()))
    else:
        if len(str_mes) > 1:
            data_in["name_in"] = str_mes.lower()
            bot.send_message(message.from_user.id, str('Поиск по должности: ' + str_mes.lower()))
        else:
            bot.send_message(message.from_user.id, 'Нужно ввести слово больше 1 буквы')
            bot.register_next_step_handler(message, get_name)


@bot.message_handler(commands=["Настроить_города"])
def area(message):
    bot.send_message(message.chat.id, 'Ниже напишите название города, где нужно искать вакансии')
    bot.register_next_step_handler(message, get_area)


def get_area(message):
    global data_in
    str_mes = str(message.text).strip()
    if len(str_mes) > 1:
        response = requests.get("https://api.hh.ru/suggests/areas?text=" + str_mes).json()
        if len(response["items"]) == 1:
            data_in["area_in"].append({"id": response["items"][0]["id"],
                                       "text": response["items"][0]["text"]})
            bot.send_message(message.from_user.id, str('Город ' + data_in["area_in"][-1]["text"] + ' добавлен в поиск'))
        elif len(response["items"]) > 1:
            str_out = "Напишите (Скопируйте) конкретное обозначение искомого города из предложенных ниже:\n"
            for q in response["items"]:
                str_out += str(q["text"]) + "\n"
            bot.send_message(message.from_user.id, str_out)
            bot.register_next_step_handler(message, get_area)
        else:
            bot.send_message(message.from_user.id, 'Городов с подобным названием не найдено')
            bot.register_next_step_handler(message, get_area)
    else:
        bot.send_message(message.from_user.id, 'Нужно ввести слово больше 1 буквы')
        bot.register_next_step_handler(message, get_area)


@bot.message_handler(commands=["Настроить_график"])
def schedule(message):
    keyboard = types.InlineKeyboardMarkup()
    key_fullDay = types.InlineKeyboardButton(text='Полный день', callback_data="0")
    keyboard.add(key_fullDay)
    key_shift = types.InlineKeyboardButton(text='Сменный график', callback_data="1")
    keyboard.add(key_shift)
    key_flexible = types.InlineKeyboardButton(text='Гибкий график', callback_data="2")
    keyboard.add(key_flexible)
    key_remote = types.InlineKeyboardButton(text='Удалённая работа', callback_data="3")
    keyboard.add(key_remote)
    key_flyInFlyOut = types.InlineKeyboardButton(text='Вахтовый метод', callback_data="4")
    keyboard.add(key_flyInFlyOut)
    bot.send_message(message.from_user.id, 'Выберите ниже необходимые графики работы', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global data_in
    data_in["schedule"][int(call.data)]["state"] = not data_in["schedule"][int(call.data)]["state"]


@bot.message_handler(commands=["Настроить_зарплату"])
def salary(message):
    bot.send_message(message.chat.id, 'Ниже введите размер зарплаты на которую рассчитываете')
    bot.register_next_step_handler(message, get_salary)


def get_salary(message):
    global data_in
    str_mes = str(message.text).replace(" ", "")
    try:
        i = int(str_mes)
        if i <= 0:
            bot.send_message(message.chat.id, 'Вы себя недооцениваете, вевдите значение з/п больше 0')
            bot.register_next_step_handler(message, get_salary)
        else:
            data_in["salary_in"] = str(i)
            bot.send_message(message.chat.id, 'Искать зарплату размером в ' + str(i) + 'руб')
    except ValueError:
        bot.send_message(message.chat.id, 'Введите целое число, без букв')
        bot.register_next_step_handler(message, get_salary)


@bot.message_handler(commands=["Сброс_параметров"])
def params_clean(message):
    global data_in
    data_in = {"name_in": "",
               "area_in": [],  # {"id":,"text":""}
               "schedule": [{"id": "fullDay", "text": "Полный день", "state": False},
                            {"id": "shift", "text": "Сменный график", "state": False},
                            {"id": "flexible", "text": "Гибкий график", "state": False},
                            {"id": "remote", "text": "Удалённая работа", "state": False},
                            {"id": "flyInFlyOut", "text": "Вахтовый метод", "state": False}],
               "salary_in": "",
               "company_in": "",
               "show": 20,
               "show_url": False,
               "is_filtr_mode": data_in["is_filtr_mode"]
               }
    bot.send_message(message.chat.id, 'Параметры сброшены')


@bot.message_handler(commands=["Параметры"])
def params(message):
    global data_in
    str_out = 'Поиск должности: ' + str(data_in["name_in"]) + "\n" + \
              'Поиск зарплаты в: ' + str(data_in["salary_in"]) + "руб\n" + \
              'Поиск в городе(ах): ' + str([i["text"] for i in data_in["area_in"]]) + "\n" + \
              'Поиск графика работы: '
    for i in range(5):
        if data_in["schedule"][i]["state"]:
            str_out += data_in["schedule"][i]["text"] + " "
    str_out += "\nФильтр по компании: " + str(data_in["company_in"]) + \
        "\nЧисло отображаемых вакансий(при фильтрации): " + str(data_in["show"]) + \
               "шт\nПоказывать ли ссылки(при фильтрации): " + str(data_in["show_url"])
    bot.send_message(message.chat.id, str_out)


@bot.message_handler(commands=["Найти"])
def find(message):
    global conn
    global cursor
    global data_in
    if data_in["name_in"]:
        bd.parse_vacancies(conn, cursor, data_in)
        query = f"SELECT * FROM vacancies WHERE name LIKE '%{data_in['name_in'].lower()}%' "
        if data_in["salary_in"]:
            query += f" AND salary_from <= {data_in['salary_in']} AND salary_to >= {data_in['salary_in']} "
        if data_in["area_in"]:
            query += f" AND city IN ({arr_str_to_str(t['text'] for t in data_in['area_in'])}) "
        s = []
        for i in range(5):
            if data_in["schedule"][i]["state"]:
                s.append(data_in["schedule"][i]["text"])
        if s:
            query += f" AND schedule IN ({arr_str_to_str(s)}) "
        query += "ORDER BY salary_to DESC LIMIT 20"
        cursor.execute(query)
        data = cursor.fetchall()
        print(data)
        for i in range(len(data)):
            # id, url, name, salary_from, sch, city, company, salary_to
            text_out = str(data[i][2]) + "\nз/п от " + str(data[i][3]) + " до " + str(data[i][7]) + "руб"
            text_out += "           График: " + str(data[i][4]) + "\n"
            text_out += "Город: " + str(data[i][5]) + "         "
            text_out += "Компания: " + str(data[i][6]) + "\n"
            if data_in["show_url"]:
                text_out += "Сссылка на вакансию: " + str(data[i][1])
            bot.send_message(message.chat.id, text_out)
        if len(data) == 0:
            bot.send_message(message.chat.id, "По вашему запросу ничего не найдено")
    else:
        bot.send_message(message.chat.id, "Необходимо ввести название вакансии - /Добавить_должность")
    bd.remove_duplicates(conn, cursor)


@bot.message_handler(commands=["Фильтр_вакансий"])
def filtr_menu(message):
    global data_in
    data_in["is_filtr_mode"] = True
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row("/Отфильтровать", "/start", "/help", "/Найти_вакансии", "/Параметры")
    keyboard.row("/Добавить_должность", "/Настроить_города", "/Настроить_компанию")  # добавление строки с кнопками
    keyboard.row("/Настроить_график", "/Настроить_зарплату", "/Сброс_параметров")  # добавление строки с кнопками
    keyboard.row("/К-во_отображаемых_вакансий", "/Отображать_ссылку")
    bot.send_message(message.chat.id,
                     'Здесь вы можете отфильтровать найденные вакансии. ' + \
                     'После настройки фильтров нажмите "Отфильтровать"',
                     reply_markup=keyboard)


@bot.message_handler(commands=["Отфильтровать"])
def filtr(message):
    global data_in
    query = f"SELECT * FROM vacancies WHERE salary_from > 0 "  # костыль :(
    if data_in["name_in"]:
        query += f" AND name LIKE '%{data_in['name_in'].lower()}%' "
    if data_in["salary_in"]:
        query += f" AND salary_from <= {data_in['salary_in']} AND salary_to >= {data_in['salary_in']} "
    if data_in["area_in"]:
        query += f" AND city IN ({arr_str_to_str(t['text'] for t in data_in['area_in'])}) "
    s = []
    for i in range(5):
        if data_in["schedule"][i]["state"]:
            s.append(data_in["schedule"][i]["text"])
    if s:
        query += f" AND schedule IN ({arr_str_to_str(s)}) "
    if data_in["company_in"]:
        query += f" AND company LIKE '%{data_in['company_in'].lower()}%' "
    query += f"ORDER BY salary_to DESC LIMIT {data_in['show']}"
    cursor.execute(query)
    data = cursor.fetchall()
    print(data)
    for i in range(len(data)):
        # id, url, name, salary_from, sch, city, company, salary_to
        text_out = str(data[i][2]) + "\nз/п от " + str(data[i][3]) + " до " + str(data[i][7]) + "руб"
        text_out += "       График: " + str(data[i][4]) + "\n"
        text_out += "Город: " + str(data[i][5]) + "     "
        text_out += "Компания: " + str(data[i][6]) + "\n"
        if data_in["show_url"]:
            text_out += "Сссылка на вакансию: " + str(data[i][1])
        bot.send_message(message.chat.id, text_out)
    if len(data) == 0:
        bot.send_message(message.chat.id, "По вашему запросу ничего не найдено, возможно стоит сделать запрос с "
                                          "данными параметрами: Найти_вакансии")


@bot.message_handler(commands=["Отображать_ссылку"])
def show_url(message):
    global data_in
    data_in["show_url"] = not(data_in["show_url"])
    if data_in["show_url"]:
        bot.send_message(message.chat.id, 'Теперь ссылки на вакансии будут отображаться.')
    else:
        bot.send_message(message.chat.id, 'Теперь ссылки на вакансии НЕ будут отображаться.')


@bot.message_handler(commands=["К-во_отображаемых_вакансий"])
def show(message):
    bot.send_message(message.chat.id, 'Ниже введите к-во выводимых вакансий за раз')
    bot.register_next_step_handler(message, get_show)


def get_show(message):
    global data_in
    str_mes = str(message.text)
    if str_mes == "":
        bot.send_message(message.chat.id, 'Нельзя ввести пустое значение')
        bot.register_next_step_handler(message, get_show)
    else:
        try:
            i = int(str_mes)
            if i <= 0:
                bot.send_message(message.chat.id, 'Нельзя вывести меньше 1 строки')
                bot.register_next_step_handler(message, get_show)
            else:
                data_in["show"] = i
                bot.send_message(message.chat.id, f'Теперь к-во отображаемых вакансий за раз: {str(data_in["show"])}')
        except ValueError:
            bot.send_message(message.chat.id, 'Введите целое число, без букв')
            bot.register_next_step_handler(message, get_show)


@bot.message_handler(commands=["Настроить_компанию"])
def company(message):
    bot.send_message(message.chat.id, 'Ниже напишите название компании')
    bot.register_next_step_handler(message, get_company)


def get_company(message):
    global data_in
    str_mes = str(message.text).strip()
    data_in["company_in"] = str_mes.lower()
    if len(data_in["company_in"]) > 0:
        bot.send_message(message.from_user.id, str('Фильтр по компании: ' + str_mes.lower()))
    else:
        bot.send_message(message.from_user.id, str('Фильтр: "любая компания"'))


bot.polling(none_stop=True, interval=1)
