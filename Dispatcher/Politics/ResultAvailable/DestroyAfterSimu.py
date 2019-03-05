import time

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class DestroyAfterSimu(object):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._kwargs = kwargs
        self._args = args

    def run(self, *args, **kwargs):
        if __debug__:
            logger.info("Destroy instance after receiving a Done message")
        return (True, kwargs["message"], {"priority": time.time()})
