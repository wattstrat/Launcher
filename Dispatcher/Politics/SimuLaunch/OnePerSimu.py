import datetime

import Config.config as config
import Config.variables as variables

from Dispatcher.Politics.SimuLaunch.SimuLaunch import SimuLaunch

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class OnePerSimu(SimuLaunch):
    def run(self, *args, **kwargs):
        if __debug__:
            logger.info("Create one instance per simulation")
        ret = super().run(*args, **kwargs)
        subscription = kwargs['message']['subscription_name']
        instance_type = config.instance_from_subscription.get(
            subscription, config.instance_from_subscription['default'])
        self.start_instance(instance_type)
        return ret

    def start_instance(self, instance_type):
        if __debug__:
            logger.info("Launching instance")
        variables.MeteorAWS.create(instance_type, 1, 1)
