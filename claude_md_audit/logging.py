import logging
import logging.config
from log_with_context import add_logging_context, Logger
import os
import sys
from claude_md_audit.env import log_level

# Setup logging
logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "simple": {"()": "claude_md_audit.logging_cli_formatter.CustomFormatter"},
        },
        "handlers": {
            "console": {
                "formatter": "simple",
                "class": "logging.StreamHandler",
            }
        },
        "loggers": {
            "": {"handlers": ["console"], "level": log_level},
        },
    }
)

# push warnings through the logger
logging.captureWarnings(True)


def setup_logging(name):
    logger = Logger(name)
    logger.level = logger.base_logger.level  # hack to fix issues with slack SDK
    return logger
