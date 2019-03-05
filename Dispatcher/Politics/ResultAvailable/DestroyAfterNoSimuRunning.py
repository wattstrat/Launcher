import datetime

import Config.variables as variables

from Dispatcher.Politics.ResultAvailable.ResultAvailable import ResultAvailable

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class DestroyAfterNoSimuRunning(ResultAvailable):
    def run(self, *args, **kwargs):
        if __debug__:
            logger.info("Destroy instance after all simu are done")
        ret = super().run(*args, **kwargs)
        with variables.lock_sec:
            if variables.simulations_en_cours == 0:
                self.destroy_all_meteor()

        return ret

    def destroy_all_meteor(self):
        if __debug__:
            logger.info("All simulation should be done. Destroy instances")
        insts = variables.MeteorAWS.get_instances()
        # In case of pending instances
        p_insts = variables.MeteorAWS.get_pending_instances()
        insts.update(p_insts)
        for inst_id, inst in insts.items():
            if __debug__:
                logger.info("Destroy instances %s", inst_id)
            inst.terminate()
