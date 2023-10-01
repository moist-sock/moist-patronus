import logging
from logging.config import dictConfig
import pathlib


class Settings:
    def __init__(self):
        self.moist_id = 272945366029172748

        self.BASE_DIR = pathlib.Path(__file__).parent.parent

        self.COGS_DIR = self.BASE_DIR / "cogs"

        self.LOGGING_CONFIG = {
            "version": 1,
            "disabled_existing_loggers": False,
            "formatters": {
                "verbose": {
                    "format": "%(levelname)-10s - %(asctime)s - %(module)-15s : %(message)s"
                },
                "standard": {"format": "%(levelname)-10s - %(name)-15s : %(message)s"},
            },
            "handlers": {
                "console": {
                    "level": "DEBUG",
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                },
                "console2": {
                    "level": "WARNING",
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                },
                "file": {
                    "level": "INFO",
                    "class": "logging.FileHandler",
                    "filename": "logs/infos.log",
                    "mode": "w",
                    "formatter": "verbose",
                },
            },
            "loggers": {
                "bot": {"handlers": ["console"], "level": "INFO", "propagate": False},
                "discord": {
                    "handlers": ["console2", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }

        dictConfig(self.LOGGING_CONFIG)
