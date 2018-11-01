import telegram

from mbs.scripts.mbs_bill import get_bill_for_the_month

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


def send_mess_bill_notification():
    # TODO: Load token at run time.
    # TODO: Load due date.
    bot = telegram.Bot(token='MBS')
    bills_for_month = get_bill_for_the_month()
    billed_month = None

    if bills_for_month:
        bill = bills_for_month[0]
        billed_month = str(bill['billed_key'])[4:]
        billed_month = index_to_month[billed_month]

    for bill in bills_for_month:
        user_id = bill['T_id']
        message = 'Bill has been generated for the month of ' + str(billed_month) + '\nAmount due is ' + str(
            bill['cost'])
        bot.send_message(user_id, message)


send_mess_bill_notification()
