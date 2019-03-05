import datetime

import Config.variables as variables

from CronJobs.MeteorOperations import MeteorDestroyInstanceBeforePayTime
from Dispatcher.Politics.ResultAvailable.ResultAvailable import ResultAvailable

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


"""
Destroy instance but wait a little to consume all the paied hour
"""


class DestroyAfterSimuWithinHour(ResultAvailable):
    def run(self, *args, **kwargs):
        ret = super().run(*args, **kwargs)
        if __debug__:
            logger.info("Pogramming Destroy instance after receiving a Done message")
        # Keep default data
        job = MeteorDestroyInstanceBeforePayTime()
        # Check immediatly
        job.run()
        return ret
