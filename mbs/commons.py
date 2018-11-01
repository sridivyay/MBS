import json
from datetime import datetime

default_db_config = {
    "user": "user1",
    "password": "user1",
    "host": "127.0.0.1"
}

ten_space = '          '
twenty_space = ten_space + ten_space
two_space = '  '


def load_database_config(file_path):
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
    if hour >= 0 and hour < 30:
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


def get_formatted_billed_detail(record):
    purchase_time = datetime.strptime(str(record['purchase_time']), '%Y-%m-%d %H:%M:%S')
    item_name = (str(record['Item_name']).ljust(20, ' '))[0:20]
    cost = str(record['cost']).ljust(6, ' ')
    quantity = str(record['qty']).ljust(16, ' ')
    billed_detail = "%s %s %s %s\n" % (item_name, quantity, cost, str(purchase_time))
    return billed_detail


def get_billed_details(db_result):
    bill_details = ''
    if db_result:
        bill_details = ''
        cost = 0
        for record in db_result:
            bill_details = bill_details + get_formatted_billed_detail(record)
            cost = cost + record['cost']
        bill_details = bill_details + '\n\nBill for month until now is ' + str(record['cost'])
    return bill_details


def get_billed_history(db_result):
    bill_details = ''
    for record in db_result:
        bill_details = bill_details + str(record['billed_month']) + '     ' + str(record['cost']) + '\n'
    return bill_details
