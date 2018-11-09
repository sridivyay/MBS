from mbs.mbs_database_access import execute_query
from mbs.mbs_log import init_logger

mbs_common_logger = init_logger()


def get_menu_for_day(weekday):
    mbs_common_logger.info('Getting menu for the weekday ' + str(weekday))
    sql_stmt = 'select * from menu_table where Day=%s'
    parms = (weekday,)
    db_result = execute_query(sql_stmt, parms, 1)
    regular = []
    extra = []
    for record in db_result:
        if record['Extra'] == 'Y':
            extra.append(record['Item_name'])
        else:
            regular.append(record['Item_name'])
    regular_menu = ",".join(regular)
    extra_menu = ",".join(extra)
    menu = 'Regular Menu: \n' + regular_menu + '\n' + 'Extra Menu: \n' + extra_menu
    return menu
