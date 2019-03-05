import time
import datetime
import threading

import Config.variables as variables
from babel.messages import JOBS
from CronJobs.CronJob import CronJob

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class MeteorDestroyInstanceBeforePayTime(CronJob):
    # TODO: if multiple DISPATCHER (HA), use tags / filters!
    _lock = threading.Lock()
    _ids = []

    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._delta_soft = kwargs.get("soft_delta", {'minutes': 5})
        self._delta_hard = kwargs.get("hard_delta", {'minutes': 2})
        self._id = kwargs.get("inst_id", None)
        self._pay_step = kwargs.get("pay_step", {'hours': 1})

        if not isinstance(self._delta_soft, dict):
            raise TypeError("Soft delta should be a dict")

        if not isinstance(self._delta_hard, dict):
            raise TypeError("Hard delta should be a dict")

        if not isinstance(self._pay_step, dict):
            raise TypeError("Pay step should be a dict")

        self._delta_soft = datetime.timedelta(**self._delta_soft)
        self._delta_hard = datetime.timedelta(**self._delta_hard)
        # we should have enough time to kill the instance
        self._delta_select = (self._delta_soft + self._delta_hard) / 2
        self._pay_step = datetime.timedelta(**self._pay_step)
        self._inst = None

        instances = variables.MeteorAWS.get_instances()

        if self._id is None:
            # Get correct server ID
            # TODO remove depending on subscription
            with MeteorDestroyInstanceBeforePayTime._lock:
                deltas = {id_inst: (datetime.datetime.now(datetime.timezone.utc) - inst.launch_time) % self._pay_step
                          for (id_inst, inst) in instances.items()
                          if id_inst not in MeteorDestroyInstanceBeforePayTime._ids}
                for inst, delt in deltas.items():
                    if __debug__:
                        logger.debug("Instance %s : time consumed since pay %s", inst, delt)
                try:
                    self._id = max(deltas, key=lambda k: deltas[k] if deltas[k] < self._pay_step - self._delta_select
                                   else datetime.timedelta(0))
                    MeteorDestroyInstanceBeforePayTime._ids.append(self._id)
                except ValueError:
                    # no one....
                    self._id = None

        self._inst = instances.get(self._id, None)

    def _run(self, *args, **kwargs):
        if self._id is None:
            # Selection of ID failed... put jobs on hold
            # Be sure we get a new inst id (should not happend...)
            if "inst_id" in self.cron_message["init_kwargs"]:
                del self.cron_message["init_kwargs"]["inst_id"]
            self.send(self._delta_soft)

        if self._inst is not None:
            launch = self._inst.launch_time
            now = datetime.datetime.now(datetime.timezone.utc)
            delta = self._pay_step - (now - launch) % self._pay_step
            if __debug__:
                logger.debug("time before shutdown : %s", delta)
            # Instance running
            # TODO : if selected instance is inside delta_hard...
            if delta < self._delta_hard:
                if __debug__:
                    logger.error("FORCE TERMINATION of %s", self._id)
                self._inst.terminate()
                # TODO : Run Cron Jobs to Clean MeteorDestroyInstanceBeforePayTime._ids
            elif delta < self._delta_soft:
                # TODO
                # SSH & soft kill
                if __debug__:
                    logger.debug("Soft termination of %s", self._id)
                self.cron_message["init_kwargs"]["inst_id"] = self._id
                self.send(delta-self._delta_hard)
            else:
                # Delta not reach : resend it and check just in time
                self.cron_message["init_kwargs"]["inst_id"] = self._id
                # not used / changed : keep it for templating
                # self.cron_message.update({'run_kwargs': kwargs, 'run_args': list(args)})
                if __debug__:
                    logger.debug("%s : delta: %s / program to now + %s", self._id, delta, delta-self._delta_soft)
                self.send(delta-self._delta_soft)
