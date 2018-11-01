import MySQLdb

from mbs.commons import default_db_config
from mbs.mbs_exceptions import InsertionFailed

config = default_db_config


def set_config(t_config):
    global config
    config = t_config
    config["database"] = 'mess'


def establish_connection():
    try:
        conn = MySQLdb.connect(**config)
        return conn
    except MySQLdb.Error as e:
        print("Error %d: %s" % (e.args[0], e.args[1]))


def execute_query(sql, parms=(), type=0):
    conn = establish_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(sql, parms)
    conn.close()
    return cursor.fetchall()


def insert_details(sql, parms):
    conn = establish_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    try:
        result = cursor.execute(sql, parms)
        conn.commit()
        conn.close()

    except MySQLdb.Error as e:
        conn.rollback()
        conn.close()

        raise InsertionFailed(e.args[0])
    return result
