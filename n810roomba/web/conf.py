import os.path


def log_function(handler):
    print 'log_function', handler

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "debug": True,
    'log_function': log_function,
    }

