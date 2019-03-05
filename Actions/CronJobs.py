from threading import Thread
import time
import datetime

from Global.Global import GlobalFiltered, ClassNotAuthorized, ModuleNotAuthorized

import Config.config as config
import Config.variables as variables

from babel.queue import RedisPriorityQueue, Consumer, Producer

from babel.messages import JOBS

import ast

if __debug__:
    import logging
    import pprint
    logger = logging.getLogger(__name__)
    pp = pprint.PrettyPrinter(indent=4)


class CronJobs(Thread, Producer, Consumer):
    """
    CronJobs handler
    """

    def __init__(self, cron_queue, delta=1):
        Thread.__init__(self)
        Producer.__init__(self, queue=cron_queue)
        Consumer.__init__(self, queue=cron_queue)

        if not isinstance(cron_queue, RedisPriorityQueue):
            raise TypeError("Use only RedisPriorityQueue for CronJobs")

        self._jobs_loader = GlobalFiltered(alias=config.CRONJOBS_ALIAS,
                                           filters=config.ALLOWED_CRONJOBS)
        self._delta = datetime.timedelta(seconds=delta)

        if __debug__:
            logger.debug("Initialization CronJobs handler (%s) with allowed jobs : %s ...",
                         cron_queue, config.ALLOWED_CRONJOBS)
        self._queue = cron_queue

    def run(self):
        """Dispatch action."""

        if __debug__:
            logger.debug("Launch the consume")
        # We have handler so we need to timeout on read operation in REDIS
        self._consume(timeout=config.DEFAULT_REDIS_TIME, sleep_time=10)

    def stop(self):
        Consumer.stop(self)
        # Clear CronJobs Queues
        self._queue.clear()

    def handle_message(self, message, queue=None):
        event = message['event']
        if event != JOBS:
            if __debug__:
                logger.error("CronJobs should be jobs event, not %s", event)
        if message["type"] != "cronjobs" or "time" not in message:
            if __debug__:
                logger.error("CronJobs should be cronjobs jobs type, not %s and time parameter must be set",
                             message["type"])

        if message["time"] - datetime.datetime.now(datetime.timezone.utc).timestamp() > self._delta.total_seconds():
            if __debug__:
                logger.debug("CronJobs must wait %d seconds",
                             message["time"] - datetime.datetime.now(datetime.timezone.utc).timestamp())
            self.emit(message, priority=int(message["time"]))
            return False

        self._run_jobs(message)

    def _run_jobs(self, request):
        if __debug__:
            logger.debug("Launching CronJob")
        args = {
            "init_args": [],
            "init_kwargs": {},
            "run_args": [],
            "run_kwargs": {}
        }

        # Get options
        for option in ["init_args", "init_kwargs", "run_args", "run_kwargs"]:
            if option in request:
                try:
                    args[option] = ast.literal_eval(request[option])
                except Exception as e:
                    if __debug__:
                        logger.error("Get exception when converting %s in python literal : %s", option, str(e))

        if request["type"] == "cronjobs":
            try:
                job = self._jobs_loader.get_instance(request["module"],
                                                     *args["init_args"],
                                                     **args["init_kwargs"])
                retcal = job.run(*args["run_args"], **args["run_kwargs"])
            except ModuleNotAuthorized as e:
                if __debug__:
                    logger.error("Try to load an unauthorized module '%s", request["module"], e)
                return False
            except ClassNotAuthorized as e:
                if __debug__:
                    logger.error("Try to load an unauthorized class '%s", request["module"], e)
                return False
            except ImportError as e:
                if __debug__:
                    logger.error("Error importing class '%s' : %s", request["module"], e)
                return False
        else:
            return False

        if __debug__:
            logger.debug("Jobs returns '%s'", retcal)
        return True


def launch(args, others):
    config.ALLOWED_CRONJOBS = ["CronJobs.%s" % (job) for job in args.allowed_cronjobs]
    init_cronjobs = ["CronJobs.%s" % (job) for job in args.initial_cronjobs]
    config.ALLOWED_CRONJOBS.extend(init_cronjobs)

    # Initialise globals vars
    cron_queue = RedisPriorityQueue([config.REDIS_QUEUE_NAME_CRONJOBS], variables.redis)
    cron = CronJobs(cron_queue, delta=args.cron_delta)

    variables.jobshandler = cron
    variables.actions_thread.append(cron)

    # First run of initial cronjobs

    for str_job in init_cronjobs:
        try:
            job = cron._jobs_loader.get_instance(str_job)
            job.initial()
        except ModuleNotAuthorized as e:
            if __debug__:
                logger.error("Try to load an unauthorized module 'CronJobs.%s' : %s", request["module"], e)
        except ClassNotAuthorized as e:
            if __debug__:
                logger.error("Try to load an unauthorized class 'CronJobs.%s' : %s", request["module"], e)
        except ImportError as e:
            if __debug__:
                logger.error("Error importing class '%s' : %s", request["module"], e)


def parser(parent_parser):
    parser = parent_parser.add_parser('cronjobs', help='cronjobs command help', aliases=['c', 'cron'])
    parser.add_argument('--cron-delta', type=float, default=1,
                        help='Cron delta-time')
    parser.add_argument('--initial-cronjobs', type=str, nargs='+', default=[],
                        help='initial jobs to start')
    parser.add_argument('--allowed-cronjobs', type=str, nargs='+', default=[],
                        help='allowed jobs to start')

    parser.set_defaults(action=launch)
    return parser
