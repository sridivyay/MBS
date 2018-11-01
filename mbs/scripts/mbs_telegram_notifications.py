import datetime
import os
import sys
from pathlib import Path

import telegram
from mbs.scripts.mbs_bill import get_bill_for_the_month
from mbs.mbs_log import init_logger
from mbs.commons import index_to_month, load_initial_configuration, get_parent_dir, get_config_file_path


def send_mess_bill_notification():
    try:
        mbs_common_logger = init_logger()
        config_path = get_config_file_path(str(os.path.realpath(__file__)))
        intial_configuration = load_initial_configuration(config_path)
        mbs_common_logger.critical('Loaded the configuration for the mess bill')
        token = str(intial_configuration["telegram_token"])
        due_date = str(intial_configuration["due_date"])
        bot = telegram.Bot(token=token)
        curr_month = datetime.datetime.today().month
        bills_for_month = get_bill_for_the_month(config_path)
        billed_month = None

        if bills_for_month:
            bill = bills_for_month[0]
            billed_month = str(bill['billed_key'])[4:]
            billed_month = index_to_month[billed_month]

        for bill in bills_for_month:
            user_id = bill['T_id']
            message = 'Bill has been generated for the month of ' + str(billed_month) + '\nAmount due is ' + str(
                bill['cost']) + '\n Due date is ' + str(due_date) + '\n You can pay by /paybill'
            bot.send_message(user_id, message)
            mbs_common_logger.info('Message sent to the user ' + str(user_id))
    except Exception as e:
        mbs_common_logger.critical(e)
        print(sys.exc_info())


