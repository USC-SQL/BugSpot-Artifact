import logging
import sys
from argparse import ArgumentParser


class StdErrorFilter(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, *blacklist):
        self.logger = logger
        self.blacklist = blacklist
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            if any(t in line for t in self.blacklist):
                continue
            self.logger.log(logging.ERROR, line.rstrip())

    def flush(self):
        pass


class LogFilter(logging.Filter):
    def __init__(self, project_name):
        self.project_name = project_name

    def filter(self, record):
        if record.name.startswith(self.project_name):
            return 1
        else:
            return 0


def parse_logger_args(parser: ArgumentParser):
    parser.add_argument("-verbose", help="By specifying this flag, the logger will output more debugging information", default=False, action="store_true")


FORMAT = '%(asctime)s [%(levelname)s] [%(name)s] [%(filename)s-%(lineno)d] %(message)s'
handlers = [logging.StreamHandler(sys.stdout)]

logging.basicConfig(
    format=FORMAT,
    handlers=handlers,
    datefmt='%m/%d/%Y %H:%M:%S'
)
for handler in logging.root.handlers:
    handler.addFilter(LogFilter('reproduce'))


def get_logger(name, logger_level=logging.DEBUG):
    logger = logging.getLogger(
        "reproduce:" + name)  # each tagger name has to be added with a prefix, this prefix is used to filter out logs from other modules
    logger.setLevel(logger_level)
    return logger

# stderr_logger = get_logger('stderr')
# sys.stderr = StdErrorFilter(stderr_logger, 'init')
