class MessMenu:
    # 0 is breakfast , 1 is lunch, 2 is dinner

    def __init__(self):
        self.slot_menu_regular = {}
        self.slot_menu_extra = {}
        self.slot_menu_regular_item_name = {}
        self.slot_menu_extra_item_name = {}

        for i in range(0, 3):
            self.slot_menu_regular[str(i)] = []
            self.slot_menu_extra[str(i)] = []

    def get_slot_menu_regular(self, slot):
        return self.slot_menu_regular[str(slot)]

    def get_slot_menu_extra(self, slot):
        return self.slot_menu_extra[str(slot)]

    def get_slot_menu_extra_item_name(self, slot):
        return self.slot_menu_extra_item_name[str(slot)]

    def get_slot_menu_regular_item_name(self, slot):
        return self.slot_menu_regular_item_name[str(slot)]

    def set_slot_menu_regular(self, slot, regular_menu):
        try:
            self.slot_menu_regular_item_name[str(slot)] = self.slot_menu_regular_item_name[str(slot)] + '\n' + \
                                                          regular_menu['Item_name']
        except KeyError:
            self.slot_menu_regular_item_name[str(slot)] = regular_menu['Item_name']

        self.slot_menu_regular[str(slot)].append(regular_menu)

    def set_slot_menu_extra(self, slot, extra_menu):
        self.slot_menu_extra[str(slot)].append(extra_menu)
        try:
            self.slot_menu_extra_item_name[str(slot)] = self.slot_menu_extra_item_name[str(slot)] + '\n' + extra_menu[
                'Item_name'] + \
                                                        'a'  # + extra_menu['Price']
        except KeyError:
            self.slot_menu_extra_item_name[str(slot)] = extra_menu['Item_name']  # + extra_menu['Price']


class MBSConfiguration:
    def __init__(self, database_config, token ):
        self.database_config = database_config
        self.token = token
