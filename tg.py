import telebot, pymysql, datetime, json, requests, subprocess, os, configparser

#Load config file
config = configparser.ConfigParser()
config.read('settings.ini')

#Starts vars
token              = config['TG']['token']
bot                = telebot.TeleBot(token)
last_count         = 0
admins_chat_id_arr = [config['TG']['admin_chat_id']]

#Keyboard load
keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard1.row('/info', '/help', '/errors')
keyboard1.row('/execute')

"""Декоратор ответа на стартовое сообщение"""
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id,'Hello world, men!', reply_markup=keyboard1)

@bot.message_handler(commands=['info'])
def cmd_info(message):
    global last_count
    con = pymysql.connect(
            host=config['DB']['host'], 
            user=config['DB']['login'], 
            password=config['DB']['password'], 
            db=config['DB']['db'])
    cursor = con.cursor()
    template = """
    👹 DATABASE INFO {} 👹

    🚨Находится {} записей
    🚨После последнего запроса добавлено {} записей
            """

    cursor.execute("SELECT COUNT(*) FROM resumes")
    all_count = cursor.fetchall()[0][0]
    bot.send_message(message.chat.id, template.format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), all_count,
                                                      all_count - last_count))
    last_count = all_count

@bot.message_handler(commands=['help'])
def cmd_help(message):
    bot.send_message(message.chat.id, """⭕️Функционал бота на данный момент

    ⚙️ /help - помощь
    ☎️ /info - актуальная информация о состоянии базы данных
    🩸 /errors - показать имеющиеся ошибки и получить отчёт""")

@bot.message_handler(commands=['errors'])
def error_info(message):
    file = open('log\\bad.log', 'r', encoding='utf-8')
    bot.send_message(message.chat.id, 'Найдено {} ошибок. Ниже отчёт'.format(len(file.readlines())))
    file.close()

    f = open("log\\bad.log", "rb")
    bot.send_document(message.chat.id, f)
    f.close()


@bot.message_handler(commands=['getdump'])
def get_dump(message):
    if !user_is_admin(message):
        return

    returned_output = subprocess.check_output('C:\\xampp\\mysql\\bin\\mysqldump -h localhost -u user -p1234 course ')
    fileName = 'dumps\\dump_{}.sql'.format(datetime.datetime.now().strftime("%d-%m-%Y_%H-%M"))
    file = open(fileName, 'w+', encoding='utf-8')
    file.write(returned_output.decode("utf-8"))
    file.close()

    file = open(fileName, 'rb')
    bot.send_document(message.chat.id, file)
    file.close()

@bot.message_handler(commands=['execute'])
def execute(message):
    if !user_is_admin(message):
        return

    bot.send_message(message.chat.id, 'Запуск параллельного парсинга hh стрницу\nНужна ссылка для парсинга из страницы поиска')

    @bot.message_handler(content_types=['text'])
    def tmp(message):
        print(message.text)
        print('r\"' + message.text + '\"')
        subprocess.Popen(
            ['python', os.path.realpath(__file__).replace('<input>', 'parser.py'), 
            'r\"' + message.text + '\"'], 
            close_fds=True)

    bot.register_next_step_handler(message, tmp)

@bot.message_handler(commands=['actives'])
def actives_bd(message):
    if !user_is_admin(message):
        return

    file = json.loads(open(config['PATH']['ip_file'], 'r').read())
    bot.send_message(
        message.chat.id, 
        '\n'.join([':'.join(data) for data in file])
    )

@bot.message_handler(commands=['add_bd'])
def add_bd(message):
    if !user_is_admin(message):
        return

    #Get data about db
    data = {}
    for field in ['host', 'user', 'password', 'db_name']:
        bot.send_message(message.chat.id, f'Введите {field} БД:')
        @bot.message_handler(content_types=['text'])
        def get_data(message):
            data[field] = message.text

        bot.register_next_step_handler(get_data)

    #Check connection
    try:
        check_con = pymysql.connect(
            host=data['host'], 
            user=data['user'], 
            password=data['password'], 
            db=data['db_name']
        )

        #Write change to file
        open(config['PATH']['ip_file'], 'w').write(json.dumps(
            json.loads(open(config['PATH']['ip_file'], 'r').read()) + [data]
        ))
    except:
        bot.send_message(message.chat.id, "Не удалось подключиться к БД")
    

def user_is_admin(message):
    if message.chat.id not in admins_chat_id_arr:
        bot.send_message(message.chat_id, "Ты не админ, тебе не зачем знать что делает эта команда!")
        return False
    return True

if __name__ == '__main__':
    bot.polling(none_stop=True)
