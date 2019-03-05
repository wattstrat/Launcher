from datetime import datetime

import Config.variables as variables
from Dispatcher.Politics.SimuLaunch.SimuLaunch import SimuLaunch
import Utils.deltas as deltas
from dateutil import parser as datetimeparser
import copy

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class SplitByYear(SimuLaunch):

    def run(self, *args, **kwargs):
        if __debug__:
            logger.info("Split simulation by year")

        ret = []
        message = kwargs["message"]
        Simus = []
        if message['simu_type'] == 'ges' or message['simu_type'] == 'scan':
            if __debug__:
                logger.info("No splitting : No simulation should have been sent, SaaS should check in Mongo only")
            pass
        elif message['simu_type'] == 'compare':
            if __debug__:
                logger.info("Getting the only interesting year")

            for index, milestone in enumerate(message['Framing_Perimeter']['milestones']):

                cArgs = copy.deepcopy(args)
                cKwargs = {"message":{}}
                cKwargs['message'] = copy.deepcopy(message)
                cKwargs["message"]['Framing_Perimeter']['period']['real_start'] = cKwargs["message"]['Framing_Perimeter']['period']['start']
                cKwargs["message"]['Framing_Perimeter']['period']['real_end'] = cKwargs["message"]['Framing_Perimeter']['period']['end']
                cKwargs['message']['Framing_Perimeter']['pertinent_milestones'] = [cKwargs["message"]['Framing_Perimeter']['period']['end']]
                cKwargs['message']['Framing_Perimeter']['milestones'] = [cKwargs["message"]['Framing_Perimeter']['period']['end']]

                cKwargs['message']['simulation_id'] += '_' + milestone

                del cKwargs["message"]["parameters"]
                cKwargs['message']['parameters'] = [message['parameters'][index]]
                
                Simus.append((cArgs, cKwargs))

        elif message['simu_type'] == 'dynamic':
            if __debug__:
                logger.info("Split simulation by year")

            real_start = message['Framing_Perimeter']['period'][
                'real_start'] = datetime.strptime(message['Framing_Perimeter']['period']['start'],'%Y-%m-%dT%H:%M:%S.%fZ')
            real_end = message['Framing_Perimeter']['period'][
                'real_end'] = datetime.strptime(message['Framing_Perimeter']['period']['end'],'%Y-%m-%dT%H:%M:%S.%fZ')
            milestones = message['Framing_Perimeter']['milestones']

            for (step_start, step_end) in deltas.deltaYears(1, real_start, real_end):
                SimuSteps = []
                pertinent_milestones = []
                [pertinent_milestones.append(0) for i in milestones]
                for index, milestone in enumerate(milestones):
                    milestone = datetime.strptime(milestone,'%Y-%m-%dT%H:%M:%S.%fZ')
                    if step_start.year == milestone.year:
                        try: 
                            sum(pertinent_milestones)
                            if index-1 >=0:
                                try:
                                    pertinent_milestones[index-1] = datetime.strptime(milestones[index-1],'%Y-%m-%dT%H:%M:%S.%fZ')
                                except IndexError:
                                    pass
                        except TypeError:
                             pass
                        pertinent_milestones[index]=milestone
                    if milestone > step_end:
                        try:
                            sum(pertinent_milestones)
                            if index-1 >=0:
                                try: 
                                    pertinent_milestones[index-1]=datetime.strptime(milestones[index-1],'%Y-%m-%dT%H:%M:%S.%fZ')
                                except IndexError:
                                    pass
                        except TypeError:
                            pass
                        pertinent_milestones[index]=milestone
                        break
                     
                cArgs = copy.deepcopy(args)
                cKwargs = {"message":{}}
                cKwargs["message"] = copy.deepcopy(message)
                cKwargs["message"]['Framing_Perimeter']['period']['start'] = ''.join((step_start.isoformat(),".000Z"))
                cKwargs["message"]['Framing_Perimeter']['period']['end'] = ''.join((step_end.isoformat(),".000Z"))
                cKwargs["message"]['Framing_Perimeter']['period']['real_start'] = ''.join((real_start.isoformat(),".000Z"))
                cKwargs["message"]['Framing_Perimeter']['period']['real_end'] = ''.join((real_end.isoformat(),".000Z"))

                del cKwargs["message"]["parameters"]
                for parameters, milestone in zip(message['parameters'], pertinent_milestones):
                    if milestone !=0:
                        if __debug__:
                            logger.debug("Handling %s => %s", step_start.isoformat(), step_end.isoformat())
                        if __debug__:
                            logger.debug("Frame %s", parameters)
                        try:
                            cKwargs["message"]["parameters"].append(parameters)
                        except (AttributeError, KeyError):
                            cKwargs["message"]["parameters"] = [parameters]
                        try:
                            cKwargs["message"]["Framing_Perimeter"]['pertinent_milestones'].append(''.join((milestone.isoformat(),".000Z")))
                        except (AttributeError,KeyError):
                            cKwargs["message"]["Framing_Perimeter"]['pertinent_milestones'] = [''.join((milestone.isoformat(),".000Z"))]

                Simus.append((cArgs, cKwargs))

        Percent = 100.0 / len(Simus)
        for (cArgs, cKwargs) in Simus:
            cKwargs["message"]["percent"] = Percent
            ret.append(super().run(*cArgs, **cKwargs))

        if len(Simus) > 1:
            with variables.lock_sec:
                variables.simulations = variables.simulations - len(Simus) + 1

        return ret
