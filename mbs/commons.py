import json
from datetime import datetime

from mbs.mbs_exceptions import TelegramTokenMissing
from mbs.mbs_log import init_logger

default_db_config = {
    "user": "user1",
    "password": "user1",
    "host": "127.0.0.1"
}
config_file_name = '/config/initial_config.json'
path = 'config/initial_config.json'

index_to_month = {"9": "September",
                  "8": "August",
                  "7": "July",
                  "6": "June",
                  "5": "May",
                  "4": "April",
                  "3": "March",
                  "2": "February",
                  "1": "January",
                  "12": "December",
                  "11": "November",
                  "10": "October"
                  }


def load_initial_configuration(config_file_path):
    mbs_common_logger = init_logger()
    mbs_common_logger.critical('Loading the configuration file')
    config_file = config_file_path + config_file_name
    with open(config_file) as data_file:
        data = json.load(data_file)

    # necessary to load telegram token
    mbs_common_logger.info('Loading telegram token')
    try:
        data["telegram_token"]
        mbs_common_logger.debug('Telegram token is ' + str(data["telegram_token"]))
    except KeyError:
        mbs_common_logger.critical('Telegram token is missing')
        raise TelegramTokenMissing()

    try:
        data["database_config"]
    except KeyError:
        # updating with the default values
        data["database_config"] = default_db_config
    mbs_common_logger.debug('database config is ' + str(data["database_config"]))

    try:
        mbs_common_logger.critical('Mess menu PDF URL is ' + str(data["mess_menu"]))
    except KeyError:
        data["mess_menu"] = None
        mbs_common_logger.critical('Mess menu PDF URL is not given')

    try:

        data["due_date"] = datetime.strptime(data["due_date"], '%Y-%m-%d')
        mbs_common_logger.critical('Due date configured is' + str(data["due_date"]))

    except KeyError:
        data["due_date"] = None
        mbs_common_logger.critical('Due date not configured ')

    except Exception as e:
        data["due_date"] = None
        mbs_common_logger.critical('Due date is wrongly configured.  Ignoring the configured date')
        mbs_common_logger.critical(e)

    try:
        data["payment_provider_token"]
        mbs_common_logger.critical('Payments are provided ')

    except KeyError:
        data["payment_provider_token"] = None
        mbs_common_logger.critical('Payments are not provided  ')

    mbs_common_logger.critical('Loading of the configuration file is complete')
    return data


def load_database_config(config_path):
    path = '/config/initial_config.json'
    file_path = str(config_path) + path
    with open(file_path) as data_file:
        data = json.load(data_file)
        try:
            database_config = data["database_config"]
        except KeyError:
            # updating with the default values
            database_config = default_db_config
        return database_config


def is_empty(structure):
    if structure:
        return False
    else:
        return True


def is_valid_slot(slot):
    hour = datetime.now().hour
    r_slot = 3
    if hour >= 8 and hour < 10:
        r_slot = 0
    elif hour >= 10 and hour < 14:
        r_slot = 1
    elif hour >= 14 and hour <= 21:
        r_slot = 2
    else:
        r_slot = 3
    if slot < r_slot:
        return False
    else:
        return True


def get_billed_history(db_result):
    bill_details = ''
    for record in db_result:
        bill_details = bill_details + str(record['billed_month']) + '     ' + str(record['cost']) + '\n'
    return bill_details


def get_parent_dir(path):
    r = str(path).rindex('/')
    return path[:r + 1]


def get_prev_month(date=datetime.today()):
    if date.month == 1:
        prev_month_timestamp = date.replace(month=12, year=date.year - 1)
    else:
        try:
            prev_month_timestamp = date.replace(month=date.month - 1)
        except ValueError:
            prev_month_timestamp = get_prev_month(date=date.replace(day=date.day - 1))
    return prev_month_timestamp.month, prev_month_timestamp.year


def get_config_file_path(path):
    index = str(path).find('/mbs') + 4
    return path[:index]
