import os
import logging


logger = logging.getLogger("varta_logger")
logger.setLevel('DEBUG')

logger_handler = logging.FileHandler(os.path.join(os.getcwd(), 'log_varta.log'))  # level=NOTSET=0
logger_error_handler = logging.FileHandler(os.path.join(os.getcwd(), 'log_error_varta.log'))
logger_error_handler.setLevel("ERROR")

logger_formatter = logging.Formatter('{asctime} - {levelname} - {message}', datefmt='%Y-%m-%d %H:%M:%S', style="{")
logger_handler.setFormatter(logger_formatter)

logger.addHandler(logger_handler)
