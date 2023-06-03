import os
from auxiliary_tools_4 import create_folder


log_dir = create_folder("logs")

logger_config = {
    'version': 1,
    'formatters': {
        'logger_formatter': {
            'format': '{asctime} - {levelname} - {message}',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'style': '{'
        }
    },
    'handlers': {
        'logger_handler': {
            'class': 'logging.FileHandler',
            # level = NOTSET(0),
            'formatter': 'logger_formatter',
            'filename': os.path.join(os.getcwd(), log_dir, 'log_varta.log'),
        },
        'logger_error_handler': {
            'class': 'logging.FileHandler',
            'level': 'ERROR',
            'formatter': 'logger_formatter',
            'filename': os.path.join(os.getcwd(), log_dir, 'log_error_varta.log'),
        }
    },
    'loggers': {
        'logger': {
            'level': 'DEBUG',
            'handlers': ['logger_handler',
                         'logger_error_handler']
        }
    }
}
