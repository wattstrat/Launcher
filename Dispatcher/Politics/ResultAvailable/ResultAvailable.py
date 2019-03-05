from babel.messages import RESULTS_AVAILABLE
import Config.variables as variables

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class ResultAvailable(object):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._kwargs = kwargs
        self._args = args

    def run(self, *args, **kwargs):
        if kwargs["message"]['event'] == RESULTS_AVAILABLE:
            if __debug__:
                logger.info("Receiving a Done message")
            with variables.lock_sec:
                if variables.simulations_en_cours > 0:
                    variables.simulations_en_cours = variables.simulations_en_cours - 1

            return (True, kwargs["message"], {})
        return (False, None, {})
