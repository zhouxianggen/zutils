import logging


def get_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        fmt = ('[%(name)-25s %(thread)-16d '
                '%(levelname)-6s %(asctime)s] %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
    return logger


class Object(object):
    def __init__(self):
        self.log = get_logger(self.__class__.__name__, logging.INFO)

