import time

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class Default(object):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._kwargs = kwargs
        self._args = args

    def run(self, *args, **kwargs):
        if __debug__:
            logger.info("Running default politics : do nothing and pass unmodified message")
        return (True, kwargs["message"], {"priority": time.time()})
