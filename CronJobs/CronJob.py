import datetime

import Config.variables as variables

from babel.messages import JOBS

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class CronJob(object):

    def __init__(self,  *args, **kwargs):
        super().__init__()

        self._delta = kwargs.get("delta", None)
        if self._delta is not None:
            self._delta = datetime.timedelta(*self._delta)

        self.cron_message = {
            'event': JOBS,
            'type': 'cronjobs',
            'module': "%s.%s" % (self.__module__, self.__class__.__name__),
            'init_kwargs': "%s" % (kwargs),
            'init_args': "%s" % (list(args)),
        }

        self._kwargs = kwargs
        self._args = args

    def _run(self, *args, **kwargs):
        raise NotImplemented("_run should be implemented")

    def _init(self, *args, **kwargs):
        if self._delta is not None:
            if __debug__:
                logger.debug("Installing recurent CronJobs %s each %d secs", __name__, self._delta.total_seconds())
            self.send()

    def run(self, *args, **kwargs):
        if __debug__:
            logger.debug("Launching %s.%s", self.__module__, self.__class__.__name__)
        self._run(*args, **kwargs)
        if self._delta is not None:
            self.send()

    def initial(self):
        if __debug__:
            logger.info("Initialiazing %s", __name__)
        self._init()

    def send(self, delta=None):
        if delta is None:
            cdelta = self._delta
        else:
            if isinstance(delta, dict):
                cdelta = datetime.timedelta(**delta)
            elif isinstance(delta, datetime.timedelta):
                cdelta = delta
            else:
                raise TypeError("delta should be dict or datetime.timedelta")
        self.cron_message["time"] = (datetime.datetime.now(datetime.timezone.utc) + cdelta).timestamp()
        if __debug__:
            logger.debug("Programming new %s.%s at %d", self.__module__,
                         self.__class__.__name__, self.cron_message["time"])
        variables.jobshandler.emit(self.cron_message, priority=int(self.cron_message["time"]))
