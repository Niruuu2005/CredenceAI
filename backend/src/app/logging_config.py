"""
Centralized logging configuration for CredenceAI.
Import and call setup_logging() once at app startup.
Format: [TIMESTAMP] [LEVEL] [MODULE] [TRACE_ID?] MESSAGE
"""
import logging
import logging.config
import sys
from app.config import settings

LOG_FORMAT = (
    "%(asctime)s.%(msecs)03d  %(levelname)-8s  %(name)-40s  %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": LOG_FORMAT,
            "datefmt": DATE_FORMAT,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "standard",
            "level": "DEBUG",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "credenceai.log",
            "maxBytes": 10 * 1024 * 1024,   # 10 MB
            "backupCount": 5,
            "formatter": "standard",
            "level": "DEBUG",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        # CredenceAI pipeline — full DEBUG
        "app": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        # Third-party — only WARNING to reduce noise
        "uvicorn": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "boto3": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "botocore": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "opensearchpy": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "handlers": [],
            "level": "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}


def setup_logging():
    """Apply the CredenceAI logging configuration."""
    logging.config.dictConfig(LOGGING_CONFIG)
    log = logging.getLogger("app.logging_config")
    log.info(
        "------------------------------------------------------------"
    )
    log.info(
        f"CredenceAI logging initialised  "
        f"[env={settings.APP_ENV}]  "
        f"[mock={settings.MOCK_SERVICES}]  "
        f"[log_level={settings.LOG_LEVEL}]"
    )
    log.info(
        "------------------------------------------------------------"
    )
