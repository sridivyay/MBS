class InsertionFailed(Exception):

    def __init__(self, error_code):
        self.error_code = error_code

    def __str__(self):
        return str(self.error_code)


class InvalidSlot(Exception):

    def __init__(self):
        self.message = 'Invalid Slot. Item not available now'

    def __str__(self):
        return self.message


class TelegramTokenMissing(Exception):

    def __init__(self):
        self.message = 'Telegram Token is not present. Cannot Start the application. Contact the admin'

    def __str__(self):
        return self.message


class BillGenerationFailed(Exception):
    error_message_mapping = {'1062': 'Bill Already generated'}

    def __init__(self, error_code):
        self.error_code = error_code
        try:
            self.message = BillGenerationFailed.error_message_mapping[str(error_code)]
        except:
            self.message = 'Insertion Failed with code'

    def __str__(self):
        return self.message + ' : ' + str(self.error_code)
