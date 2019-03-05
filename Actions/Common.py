import argparse

from configparser import ConfigParser, ExtendedInterpolation

import os
import sys
import copy
from redis import StrictRedis

import Config.config as config
import Config.variables as variables
from Config.configfile import defaultconfig

from Utils.Config import update_conf

if __debug__:
    import logging
    import logging.config
    logger = logging.getLogger(__name__)


# Configure common argument
def trait_common_args(args):
    parser = ConfigParser(interpolation=ExtendedInterpolation())

    variables.configfile = parser
    variables.config = copy.deepcopy(defaultconfig)

    if args.version:
        print(config.version)
        sys.exit(0)

    # Read actual config file
    parser.read(args.config)
    variables.configfile = parser

    arg = vars(args)

    update_conf(arg, "common")

    if __debug__:
        logconf = variables.config["common"]['logconfigfile']
        if os.path.isfile(logconf):
            logging.config.fileConfig(logconf, disable_existing_loggers=False)

        variables.logger = logging.getLogger('DISPATCHER')
        logger = logging.getLogger(__name__)

    # Load Redis
    variables.redis = StrictRedis(host=variables.config["common"]["redis_host"],
                                  port=variables.config["common"]["redis_port"])

    config.REDIS_HOST=variables.config["common"]["redis_host"]
    config.REDIS_PORT=variables.config["common"]["redis_port"]
    

    # Write current PID
    write_pid()


def write_pid():
    pid = os.getpid()
    try:
        with open(variables.config["common"]["pidfile"], 'w') as pidfile:
            pidfile.write("%d" % (pid))
    except Exception as e:
        # TODO : more specific for execption
        if __debug__:
            logger.warning("[%d] Could not write PID file (%s) : %s", pid, variables.config["common"]["pidfile"], e)
        pass


def describe(args, others):
    print(config.version)
    # For test
    print(variables.config)
    print(others)


def parser(argsparser):
    argsparser.add_argument('--loglevel', type=int, help='set log level')
    argsparser.add_argument('--logconfigfile', type=str, help='set log config file')
    argsparser.add_argument('--config', type=str, default="/etc/meteor/meteor.conf", help='config file')
    argsparser.add_argument('--version', action='store_true', default=False, help='display version')
    argsparser.add_argument('--pidfile', type=str, help='Set PID-file')

    argsparser.add_argument('--redis-host', type=str, help='Change value of the redis host')
    argsparser.add_argument('--redis-port', type=int, help='Change value of the redis port')

    argsparser.set_defaults(action=describe)
