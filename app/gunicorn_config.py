import multiprocessing
import logging

logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',  # Adjust the level as needed
    },
}

workers = multiprocessing.cpu_count() * 2 + 1
bind = '0.0.0.0:8000'
logconfig_dict['loggers'] = {
    'gunicorn.error': {
        'level': 'ERROR',
        'handlers': ['console'],
        'propagate': True,
    },
}
