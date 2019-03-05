import time
import datetime

import Config.variables as variables
from babel.messages import JOBS
from mail import MeteorStatsEmail
from CronJobs.CronJob import CronJob

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class MeteorStats(CronJob):
    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._mail = MeteorStatsEmail()
        self._delta = datetime.timedelta(hours=3)

    def _run(self, *args, **kwargs):
        ids = variables.MeteorAWS.get_instances()
        pids = variables.MeteorAWS.get_pending_instances()
        if __debug__:
            logger.debug("Active instances : %s\nPending Instances : %s", ids, pids)
        ids.update(pids)

        insts_stats = {inst_id: {"tags": "/".join(["%s=%s" % (t["Key"], t["Value"]) for t in inst.tags]),
                                 "state": inst.state["Name"],
                                 "running_time": datetime.datetime.now(datetime.timezone.utc) - inst.launch_time}
                       for inst_id, inst in ids.items()}
        if len(insts_stats) > 0:
            self._mail.send(instances_stats=insts_stats, simulations=variables.simulations_en_cours)
