import telebot, pymysql, datetime, json, requests, subprocess, os, configparser, re
from api.api import ApiParser

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
keyboard1.row('/execute', '/getdump')

"""Декоратор ответа на стартовое сообщение"""
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id,'Hello, men!', reply_markup=keyboard1)

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
    🩸 /errors - показать имеющиеся ошибки и получить отчёт
    📄 /getdump - получить дамп базы в .sql""")

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
    if not user_is_admin(message):
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
def execute_answer(message):
    if not user_is_admin(message):
        return

    params = {
        'mode' : '',
        'url'  : ''
    }

    bot.send_message(message.chat.id, 'Запуск парсинга hh стрницу\nНужна ссылка для парсинга из страницы поиска\nВыберите режим:')
    bot.send_message(message.chat.id, 'all или current')

    def execute_mode(message):
        params['mode'] = message.text
        bot.send_message(message.chat.id, 'Введите url')

        def execute_start(messsage):
            params['url'] = message.text

            table_active = []
            file = json.loads(open(config['PATH']['ip_file'], 'r').read())
            for ip, token in file.items():
                try:
                    table_active.append({
                        'ip' : ip,
                        'token' : token,
                        'count' : int(ApiParser(ip, token).parse_status())
                    })
                except:
                    pass

            table_active = sorted(table_active, key=lambda x: x['count'])
            current_parser = ApiParser(
                table_active[0]['ip'], 
                table_active[0]['token']
                )

            current_parser.execute_parse(params['url'], params['mode'])


        bot.register_next_step_handler(message, execute_start)

    bot.register_next_step_handler(message,execute_mode)



@bot.message_handler(commands=['actives'])
def actives_bd(message):
    if not user_is_admin(message):
        return

    file = json.loads(open(config['PATH']['ip_file'], 'r').read())

    for ip, token in file.items():
        try:
            count = int(ApiParser(ip, token).parse_status())
            bot.send_message(
                message.chat.id, 
            ('🟢 ' if count > 0 else '🔴 ') + ip + ' : ' + str(count)
            )
        except:
            bot.send_message(message.chat.id, 'Проблемы на ' + ip)

def check_connection_data(message):
    answer = re.findall(r'([^;]+);([^;]+)', message.text)[0]
    
    try:
        fields = ['host', 'token']
        for field in fields:
            data[field] = answer[fields.index(field)]

        res = ApiParser(data['host'], data['token'])
        bot.send_message(message.chat.id, "API соединение успешно установлено")

        ip_dict = json.loads(open(config['PATH']['ip_file'], 'r').read())
        ip_dict[data['host']] = data['token']

        with open(config['PATH']['ip_file'], 'w') as outfile:
            json.dump(ip_dict, outfile)
    except:
        print("fack")


@bot.message_handler(commands=['add_api'])
def add_api(message):
    if not user_is_admin(message):
        return

    #Get data about db
    global data
    data = {}
    bot.send_message(message.chat.id, f'Введите данные в формате `host;token`')
    msg = bot.send_message(message.chat.id, f'Example: https://192.168.35.200/api.php;MY_SUPER_PUPER_TOKEN')
    bot.register_next_step_handler(msg, check_connection_data)
   
    




def user_is_admin(message):
    if str(message.from_user.id) not in admins_chat_id_arr:
        bot.send_message(message.chat.id, "Ты не админ, тебе не зачем знать что делает эта команда!")
        return False
    return True

if __name__ == '__main__':
    bot.polling(none_stop=True)
