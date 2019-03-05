import datetime

import Config.variables as variables

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class SimuLaunch(object):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._kwargs = kwargs
        self._args = args

    def run(self, *args, **kwargs):
        with variables.lock_sec:
            variables.simulations_en_cours = variables.simulations_en_cours + 1
        if __debug__:
            logger.debug("Sending message %s", kwargs["message"])
        return (True, kwargs["message"], {"priority": datetime.datetime.now(datetime.timezone.utc).timestamp()})
