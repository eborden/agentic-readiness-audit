import logging
from datetime import datetime, timezone
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

colorama_init()


class CustomFormatter(logging.Formatter):

    def format(self, record):
        msg = f"{Fore.BLUE}{datetime.now(timezone.utc)} "
        msg += f"{logLevelColor(record.levelno)}[{record.levelname}] {Style.RESET_ALL}"
        msg += f"{record.name}:{record.lineno} "
        msg += f"{logLevelColor(record.levelno)}{record.getMessage()} {Style.RESET_ALL}"

        extra = self.extra_from_record(record)
        for prop, val in extra.items():
            msg += f"\n    {Fore.CYAN}%s={Style.RESET_ALL}%s" % (prop, val)

        return msg

    def extra_from_record(self, record):
        return {
            attr_name: record.__dict__[attr_name]
            for attr_name in record.__dict__
            if attr_name not in BUILTIN_ATTRS
        }


def logLevelColor(logLevel):
    match logLevel:
        case logging.DEBUG:
            return Fore.CYAN
        case logging.INFO:
            return Fore.GREEN
        case logging.WARNING:
            return Fore.YELLOW
        case logging.ERROR:
            return Fore.RED
        case logging.CRITICAL:
            return Fore.RED
        case logging.NOTSET:
            return Fore.BLUE


BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "taskName",
    "thread",
    "threadName",
}
