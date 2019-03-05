import threading

if __debug__:
    import logging
    # create logger
    logger = logging.getLogger('DISPATCHER')

# config
config = None
configfile = None

awsconfig = {}

# Global variable
actions_thread = []
redis = None

MeteorAWS = None
jobshandlers = None

simulations = 0
simulations_en_cours = 0
lock_sec = threading.Lock()
