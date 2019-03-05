import datetime

import Config.variables as variables

from Dispatcher.Politics.SimuLaunch.OnePerSimu import OnePerSimu
from Dispatcher.Politics.SimuLaunch.SimuLaunch import SimuLaunch

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class OnlyOnePerSimu(OnePerSimu):
    def run(self, *args, **kwargs):
        if __debug__:
            logger.info("Create Only one instance per simulation")

        start_instance = False
        with variables.lock_sec:
            num_active_instances = len(variables.MeteorAWS.get_instances())
            num_pending_instances = len(variables.MeteorAWS.get_pending_instances())
            number_instances = num_active_instances + num_pending_instances
            if __debug__:
                logger.debug("Simu : %d / Instances : %d (act: %d)", variables.simulations_en_cours,
                             number_instances, num_active_instances)
            if variables.simulations_en_cours >= number_instances:
                start_instance = True
        if start_instance:
            return OnePerSimu.run(self, *args, **kwargs)
        else:
            return SimuLaunch.run(self, *args, **kwargs)
