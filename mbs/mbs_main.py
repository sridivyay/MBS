import json

import datetime
import os
import time
from os import path

import MySQLdb
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from mbs.commons import is_empty, is_valid_slot, get_billed_details, get_billed_history, default_db_config, ten_space, \
    twenty_space
from mbs.mbs_classes import MessMenu
from mbs.mbs_database_access import execute_query, insert_details, set_config

from mbs.mbs_exceptions import InsertionFailed, TelegramTokenMissing
from mbs.mbs_log import init_logger

# globals

mbs_common_logger = None
database_config = ''
telegram_token = ''
config_file_name = '/config/initial_config.json'
pdf_file_name = '/config/dummy.pdf'

slot_vs_callback_data = [3, 5, 7]
callback_data_vs_slot = {'0': '0', '1': '1', '2': '2', '3': '0', '4': '0', '5': '1', '6': '1', '7': '2', '8': '2'}
slot_vs_message_data_map = {"0": "Breakfast", "1": "Lunch", "2": "Dinner"}
check_if_valid_button = {'B': 0, 'I': 0, 'C': 0}
mess_menu_today = MessMenu()
# TODO: Load only once at start
item_id_to_name_mapping = {}
item_id_to_price_mapping = {}
item_id_to_slot_mapping = {}

valid_users_mbs = {}
cancel_button = [InlineKeyboardButton("Cancel Order", callback_data='Cancel')]
CONTACT = range(1)
please_register_message = 'We know you are hungry. Register using /register. Yummy food is waiting.\n'

'''
    Loads initial configuration 
        Telegram token
        database config
'''


def load_initial_configuration():
    mbs_common_logger.critical('Loading the configuration file')
    config_file = path.join(path.dirname(path.abspath(__file__))) + config_file_name
    with open(config_file) as data_file:
        data = json.load(data_file)

    # necessary to load telegram token
    mbs_common_logger.info('Loading telegram token')
    try:
        global telegram_token
        telegram_token = data["telegram_token"]
        mbs_common_logger.debug('Telegram token is ' + str(telegram_token))

    except KeyError:
        mbs_common_logger.critical('Telegram token is missing')
        raise TelegramTokenMissing()

    global database_config
    try:
        database_config = data["database_config"]
    except KeyError:
        # updating with the default values
        database_config = default_db_config

    mbs_common_logger.debug('database config is ' + str(database_config))
    mbs_common_logger.critical('Loading of the configuration file is complete')


def get_item_quantity_telegram_buttons(item_button_id):
    button_list = [
        InlineKeyboardButton("1", callback_data='B1' + str(item_button_id)),
        InlineKeyboardButton("2", callback_data='B2' + str(item_button_id)),
        InlineKeyboardButton("3", callback_data='B3' + str(item_button_id))
    ]
    reply_markup = InlineKeyboardMarkup([button_list, cancel_button])
    return reply_markup


def telegram_slot_input_options():
    button_list = [
        InlineKeyboardButton("Breakfast", callback_data=0),
        InlineKeyboardButton("Lunch", callback_data=1),
        InlineKeyboardButton("Dinner", callback_data=2)
    ]
    reply_markup = InlineKeyboardMarkup([button_list, cancel_button])
    return reply_markup


def telegram_slot_menu_operations(slot):
    button_list = [
        InlineKeyboardButton("Regular", callback_data=slot_vs_callback_data[slot]),
        InlineKeyboardButton("Extra", callback_data=slot_vs_callback_data[slot] + 1),
    ]
    reply_markup = InlineKeyboardMarkup([button_list, cancel_button])
    return reply_markup


def start(bot, update):
    message = 'Hi Foodie,\nWelcome to the mess billing system.\n' \
              '/menu - To get the Menu\n' + '/bill - To get month bill\n' + '/bills - History of bills'
    mbs_common_logger.info('User ' + str(update.message.chat.id) + ' has initiated start')
    bot.send_message(chat_id=update.message.chat_id, text=message)


def daily(bot, update):
    # TODO: Read from config file
    pdf_link = 'https://s3.ap-south-1.amazonaws.com/mbsdemo/mess_menu.pdf'
    mbs_common_logger.info('User ' + str(update.message.chat.id) + ' has requested the daily menu')
    try:
        bot.sendDocument(update.message.chat_id, pdf_link)
    except Exception as e:
        mbs_common_logger.critical(e)
    mbs_common_logger.info('User ' + str(update.message.chat.id) + ' sent the daily menu')


def menu(bot, update):
    # Send buttons on today's menu depending on the slot.
    reply_markup = telegram_slot_input_options()
    mbs_common_logger.info('User ' + str(update.message.chat.id) + ' has requested the menu')
    bot.send_message(chat_id=update.message.chat_id, text='Select the menu\n',
                     reply_markup=reply_markup)


def load_all_mbs_users():
    global valid_users_mbs
    # TODO: Load users frequently
    mbs_common_logger.info('Loading the users')
    sql_stmt = 'Select T_id from user'
    parms = ()
    db_result = execute_query(sql_stmt, parms, 1)
    if not db_result:
        valid_users_mbs = None
        mbs_common_logger.debug('No users present in the table')

    for result in db_result:
        valid_users_mbs[str(result['T_id'])] = 1
    mbs_common_logger.info('Loaded the users for MBS')


def load_menu_for_day():
    global mess_menu_today
    # TODO: Update the menu daily
    # monday starts from 0
    mbs_common_logger.info('Loading the menu for MBS')
    weekday = datetime.datetime.today().weekday()
    sql_stmt = " Select * from menu_table where Day = %s"
    parms = (weekday,)
    db_result = execute_query(sql_stmt, parms, 1)
    mess_menu_today = MessMenu()

    if is_empty(db_result):
        menu_message = 'Mess is not available today'
        mbs_common_logger.info(menu_message)
    else:
        for result in db_result:
            if result['Extra'] == 'Y':
                mess_menu_today.set_slot_menu_extra(result['Time'], result)
            else:
                mess_menu_today.set_slot_menu_regular(result['Time'], result)
    mbs_common_logger.info('Loaded the menu for MBS')


def get_bill(bot, update):
    global valid_users_mbs
    user_id = update.message.chat.id
    mbs_common_logger.info('User ' + str(user_id) + ' has requested the bill')
    if valid_users_mbs[str(user_id)]:
        sql_stmt = \
            'Select Item_name, cost, qty, purchase_time from purchase_order, items where T_id = %s and Id = item_id'
        parms = (user_id,)
        db_result = execute_query(sql_stmt, parms, 1)
        # TODO: change logic to get the bill only for this month
        message = 'Your bill details are \n' + 'Item' + twenty_space + 'Quantity' + ten_space + 'Cost' + ten_space + 'Purchase_date' + '\n' + get_billed_details(
            db_result)
        mbs_common_logger.info('Bill has been sent to the User: ' + str(user_id))

    else:
        message = please_register_message
        mbs_common_logger.info('Denied getbill request for the user ' + str(user_id) + ' as not a valid user')

    bot.send_message(chat_id=update.message.chat_id, text=message)


def get_bills(bot, update):
    user_id = update.message.chat.id
    mbs_common_logger.info('User ' + str(user_id) + ' has requested the bill history')

    if valid_users_mbs[str(user_id)]:
        sql_stmt = 'Select DATE_FORMAT(billed_time,"%%Y-%%m") as billed_month, cost from bill_history where T_id = %s'
        parms = (user_id,)
        try:
            db_result = execute_query(sql_stmt, parms, 1)
        except Exception as e:
            mbs_common_logger.critical(e)
        if db_result:
            message = 'Your bill history is  \n' + 'yyyy-mm Cost\n' + get_billed_history(db_result)
        else:
            message = 'No purchase record'

    else:
        message = please_register_message
        mbs_common_logger.info('Denied bill history request for the user ' + str(user_id) + ' as not a valid user')

    bot.send_message(chat_id=update.message.chat_id, text=message)


def telegram_extra_items_buttons(slot):
    global mess_menu_today
    global item_id_to_slot_mapping
    extra_items_for_slot = mess_menu_today.get_slot_menu_extra(slot)
    if len(extra_items_for_slot) == 0:
        raise ValueError
    button_list = []
    for extra in extra_items_for_slot:
        item_id_to_name_mapping[str(extra['Item_Id'])] = extra['Item_name']
        item_id_to_price_mapping[str(extra['Item_Id'])] = int(extra['Item_price'])
        item_id_to_slot_mapping[str(extra['Item_Id'])] = slot

        button_label = extra['Item_name'] + ' - ' + str(extra['Item_price'])
        button_list.append(
            [InlineKeyboardButton(button_label, callback_data='I' + str(extra['Time']) + str(extra['Item_Id']),
                                  resize_keyboard=True)])
    button_list.append(cancel_button)
    reply_markup = InlineKeyboardMarkup(button_list)
    return reply_markup


def does_require_slot(s):
    try:
        check_if_valid_button[s]
        return 0
    except:
        return 1


def button_handlers(bot, update):
    global mess_menu_today
    global valid_users_mbs
    global item_id_to_slot_mapping

    query = update.callback_query
    check = 0
    button_call_back_data = format(query.data)
    menu_message = ''
    try:
        if does_require_slot(button_call_back_data[0]):
            slot = callback_data_vs_slot[str(button_call_back_data)]
    except ValueError:
        slot = 0
    except:
        slot = 0
    if button_call_back_data == '0' or button_call_back_data == '1' or button_call_back_data == '2':
        reply_markup = telegram_slot_menu_operations(int(format(query.data)))
        bot.edit_message_text(text=slot_vs_message_data_map[format(query.data)] + ' Menu',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id, reply_markup=reply_markup)

    elif button_call_back_data == '3' or button_call_back_data == '5' or button_call_back_data == '7':
        try:
            menu_message = 'The ' + slot_vs_message_data_map[
                slot] + ' menu is \n' + mess_menu_today.get_slot_menu_regular_item_name(slot)
        except:
            menu_message = "Sorry no " + slot_vs_message_data_map[slot] + "  menu today ".format(query.data)

    elif button_call_back_data == '4' or button_call_back_data == '6' or button_call_back_data == '8':
        menu_message = "Extras in " + slot_vs_message_data_map[slot] + " are\n"
        try:
            reply_markup = telegram_extra_items_buttons(slot)
            check = 1
        except ValueError:
            menu_message = 'No Extras in ' + slot_vs_message_data_map[slot]
            reply_markup = ''
        bot.edit_message_text(text=menu_message,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id, reply_markup=reply_markup)

    elif format(query.data[0]) == 'B':
        check = 1
        qty = button_call_back_data[1]
        item_id = button_call_back_data[4:]
        cost = int(item_id_to_price_mapping[item_id]) * int(qty)
        user_id = update.callback_query.message.chat.id
        buy_item = True
        if is_valid_slot(int(item_id_to_slot_mapping[str(item_id)])):
            try:
                sql_insert_query = """ INSERT INTO purchase_order(T_id, qty, cost, item_id,purchase_time) 
                                        VALUES (%s,%s,%s,%s,%s) """
                purchase_time = time.strftime('%Y-%m-%d %H:%M:%S')
                records_to_insert = (user_id, qty, cost, item_id, purchase_time)
                result = insert_details(sql_insert_query, records_to_insert)
            except InsertionFailed as e:
                menu_message = 'Hey foodie something was burnt. Show this message to the Administrator. ' \
                               + str(e) + ' Please try again.'
                buy_item = False
            except:
                menu_message = 'Looks like something is wrong. Show this message to the Administrator. ' \
                               + ' Please try again.'
                buy_item = False

            if buy_item:
                menu_message = 'Successfully bought ' + item_id_to_name_mapping[
                    item_id] + '\nQuantity:' + qty + '\nBilled Amount: ' + str(cost)
                mbs_common_logger.info('User: ' + str(user_id) + menu_message)
            else:
                mbs_common_logger.info('User: ' + str(user_id) + ' request failed to purchase the item ' + str(item_id))
        else:
            menu_message = 'You have to wait until next week'
            mbs_common_logger.info('User: ' + str(user_id) +
                                   ' request failed to purchase the item ' + str(item_id) + ' in wrong slot')

        bot.edit_message_text(text=menu_message,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)

    elif button_call_back_data[0] == 'I':
        user_chat_id = update.callback_query.message.chat.id
        try:
            if valid_users_mbs[str(user_chat_id)]:
                check = 1
                menu_message = 'Choose a quantity'
                reply_markup = get_item_quantity_telegram_buttons(query.data)
        except:
            # Check if present in pre reg table
            menu_message = 'We know you are hungry. Register using /register. Yummy food is waiting.\n'
            reply_markup = ''
        bot.edit_message_text(text=menu_message,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id, reply_markup=reply_markup)
        return ConversationHandler.END

    elif button_call_back_data == 'Cancel':
        menu_message = 'Cancelled. Hey foodie are you upset with the menu today.'
        bot.edit_message_text(text=menu_message,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
        return ConversationHandler.END

    if check == 0:
        bot.edit_message_text(text=menu_message,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)


def register(bot, update):
    share_contact_request = 'Please share your contact to continue the MBS'
    reply_markup = telegram.ReplyKeyboardMarkup([[telegram.KeyboardButton('Share contact', request_contact=True)]])
    bot.send_message(chat_id=update.message.chat_id, text=share_contact_request, reply_markup=reply_markup)
    return CONTACT


def register_user_in_database(bot, update, chat_data):
    global valid_users_mbs
    user_registered_successfully = True
    contact = update.effective_message.contact
    phone_number = contact.phone_number
    user_id = update.message.from_user.id
    try:

        if valid_users_mbs[str(user_id)]:
            user_registered_successfully = False
            message = 'Already registered'
    except:
        try:
            if not update.message.from_user.is_bot:
                # Comes as 91XXX hence removing 91 code
                phone_number = phone_number[2:]
                sql_stmt = 'Select * from pre_reg_user where Phone_no = %s'
                parms = (phone_number,)
                db_result = execute_query(sql_stmt, parms, 1)
                if db_result:
                    db_result = db_result[0]
                if db_result:
                    records_to_insert = (
                        db_result['roll_no'], db_result['name'], phone_number, 'Y', db_result['Hall_no'], user_id)
                    sql_insert_query = """ INSERT INTO user(roll_no, name, Phone, Active_flag, Hall_no,T_id) 
                                            VALUES (%s,%s,%s,%s,%s,%s) """
                    try:
                        result = insert_details(sql_insert_query, records_to_insert)
                        user_registered_successfully = True
                        valid_users_mbs[str(user_id)] = 'Y'

                    except InsertionFailed as e:
                        user_registered_successfully = False
                        message = 'Hey foodie something was burnt. Show this message to the Administrator. ' \
                                  + str(e) + ' Please try again.'
                    except:
                        user_registered_successfully = False
                        message = 'Looks like something is wrong. Show this message to the Administrator. ' \
                                  + ' Please try again.'

                else:
                    user_registered_successfully = False
                    message = 'Hey foodie be patient MBS is coming soon for you'

            else:
                user_registered_successfully = False
                message = 'Sorry bots can\'t be foodies'

        except MySQLdb.Error as e:
            message = 'Hey foodie something went down. Show this message to the Administrator. ' \
                      + str(e.args[0]) + ' Please try later.'
            user_registered_successfully = False

    if user_registered_successfully:
        bot.send_message(chat_id=update.message.chat_id, text='Successfully created the user id. Start fooding')
    else:
        bot.send_message(chat_id=update.message.chat_id, text=message)
    return ConversationHandler.END


def parse_user_request(bot, update, user_data=None):
    if update.message.text.lower().find('help') != -1 or update.message.text.lower().find('start') != -1 or \
            update.message.text.lower().find('hello') != -1 or update.message.text.lower().find('hi') != -1:
        start(bot, update)

    elif update.message.text.lower().find('hungry') != -1 or update.message.text.lower().find('food') != -1 or \
            update.message.text.find('menu') != -1 or update.message.text.find('bored') != -1 or \
            update.message.text.find('tired') != -1 or update.message.text.find('lazy') != -1:
        menu(bot, update)
    elif update.message.text.lower().find('daily') != -1:
        daily(bot, update)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Could not understand. use /help for more info')


def telegram_integration_code_init():
    updater = Updater(token=telegram_token)
    dispatcher = updater.dispatcher
    get_menu_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('menu', callback=menu)],
        run_async_timeout=1,
        allow_reentry=True,
        fallbacks=[],
        states={},

    )
    dispatcher.add_handler(get_menu_conversation_handler)

    start_handler = CommandHandler('start', start)
    updater.dispatcher.add_handler(start_handler)

    help_handler = CommandHandler('help', start)
    updater.dispatcher.add_handler(help_handler)

    get_bill_handler = CommandHandler('bill', get_bill)
    updater.dispatcher.add_handler(get_bill_handler)

    ge_bills_handler = CommandHandler('bills', get_bills)
    updater.dispatcher.add_handler(ge_bills_handler)

    register_handler = ConversationHandler(
        entry_points=[CommandHandler('register', callback=register)],
        states={
            CONTACT: [MessageHandler(Filters.contact, callback=register_user_in_database, pass_chat_data=True)],
        },
        fallbacks=[],
        run_async_timeout=1,
        allow_reentry=True
    )
    dispatcher.add_handler(register_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(button_handlers))

    parse_user_request_handler = MessageHandler(Filters.text, parse_user_request, pass_user_data=True)
    dispatcher.add_handler(parse_user_request_handler)

    mbs_common_logger.info('Added the handlers....')
    return updater, dispatcher


def mbs_data_update():
    mbs_common_logger.info('Loading the data')
    load_menu_for_day()
    load_all_mbs_users()
    mbs_common_logger.info('Loading the data is completed')


try:
    mbs_common_logger = init_logger()
    load_initial_configuration()
    set_config(database_config)
    mbs_data_update()
    updater, dispatcher = telegram_integration_code_init()
    updater.start_polling()

    while True:
        time.sleep(60)
        updater.stop()
        mbs_common_logger.info('Updating the cached data')
        mbs_data_update()
        mbs_common_logger.info('Starting the updater...')
        updater.start_polling()

except TelegramTokenMissing as e:
    mbs_common_logger.critical('Cannot start MBS')
