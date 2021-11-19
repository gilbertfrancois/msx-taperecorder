import logging
import logging.config
import os

LOG_TO_FILE = "LOG_TO_FILE" in os.environ

# Important: do not execute any top level logging instruction from this module unless
# there won't be a chance to initialize the logging system properly later.
def setup_logging(extra_logger_levels=None):
    if extra_logger_levels is None:
        extra_logger_levels = {}

    loggers = {}

    root_logger = {
        "level": "DEBUG",
        "handlers": ["stdout", "file"] if LOG_TO_FILE else ["stdout"]
    }

    for logger_name, level in extra_logger_levels.items():
        if logger_name == "root":
            root_logger["level"] = level
        else:
            loggers[logger_name] = {"level": level}

    logging_config = {
        "version": 1,
        "formatters": {
            "normal": {
                "format": "%(asctime)-15s (%(process)5d) [%(levelname)-8s][%(name)-25s] %(message)s"
            }
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "formatter": "normal",
                "stream": "ext://sys.stdout"
            },
        },
        "loggers": loggers,
        "root": root_logger
    }

    if LOG_TO_FILE:
        os.makedirs(f"{project_dir}/logs/", exist_ok=True)
        logging_config["handlers"]["file"] = {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "normal",
            "filename": f"{project_dir}/logs/msx-taperecorder.log",
            "when": "midnight",
            "interval": 1,
        }

    # Configure Python's logging
    logging.config.dictConfig(logging_config)
