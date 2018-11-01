import logging.config
from os import path

# globals
logger_file_path = '/config/logging.conf'


def init_logger():
    logger_config_path = path.join(path.dirname(path.abspath(__file__))) + logger_file_path
    logging.config.fileConfig(logger_config_path)
    logger = logging.getLogger('MBS_default_logger')
    return logger
