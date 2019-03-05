from threading import Thread
import time
import os

from Global.Global import GlobalFiltered, ClassNotAuthorized, ModuleNotAuthorized
import Config.config as config
import Config.variables as variables

from babel.queue import RedisPriorityQueue, RedisQueue, Consumer, Producer

from aws_interface import EC2Meteor
from Utils.Config import update_conf

if __debug__:
    import logging
    import pprint

    logger = logging.getLogger(__name__)
    pp = pprint.PrettyPrinter(indent=4)


class Dispatcher(Thread, Producer, Consumer):
    """
    Dispatch FrontEnd SaaS request to meteor Server
    Taking care of which client subscription
    """

    def __init__(self, in_queue, out_queue, politics_type, default_politic):
        Thread.__init__(self)
        Producer.__init__(self, queue=out_queue)
        Consumer.__init__(self, queue=in_queue)
        if __debug__:
            logger.debug("Initialization Dispatcher %s => %s ...", in_queue, out_queue)
        self._politics_type = politics_type
        self._global = GlobalFiltered(alias=config.POLITIC_ALIAS,
                                      filters=config.ALLOWED_POLITICS[politics_type])
        self._default_politic = default_politic

    def run(self):
        """Dispatch action."""
        if __debug__:
            logger.debug("Launch the consume")
        # We have handler so we need to timeout on read operation in REDIS
        self._consume(timeout=config.DEFAULT_REDIS_TIME)

    def handle_message(self, message, opt_handle=None, queue=None):
        politic = self._extract_politic(message)
        (args, kwargs) = self._extract_opt_politic(message)
        (margs, mkwargs) = self._extract_opt_msg(message)

        msg_class = "Dispatcher.Politics.%s.%s" % (self._politics_type, politic)
        ret = False
        for act in [msg_class, config.__DEFAULT_HANDLER_CLASS__[self._politics_type]]:
            try:
                message_handler = self._global.get_instance(act, *args, message=message, **kwargs)
                retMess = message_handler.run(*margs, message=message, **mkwargs)
                if type(retMess) is not list:
                    retMess = [retMess]
                for (ret, message_ret, opt) in retMess:
                    # We trait the message correctly, emit the message
                    if ret:
                        self.emit(message_ret, **opt)
                break
            except ModuleNotAuthorized as e:
                if __debug__:
                    logger.error("Try to load an unauthorized module '%s' : %s", act, e)
                continue
            except ClassNotAuthorized as e:
                if __debug__:
                    logger.error("Try to load an unauthorized class '%s' : %s", act, e)
                continue
            except ImportError as e:
                if __debug__:
                    logger.error("Error importing class '%s' : %s", act, e)
                continue
        return ret

    def _extract_politic(self, message):
        # TODO
        return self._default_politic

    def _extract_opt_politic(self, message):
        # TODO
        kwargs = {}
        args = []
        if not isinstance(kwargs, dict):
            if __debug__:
                logger.error("Politic kwargs not a dict")
            kwargs = {}
        if not isinstance(args, list):
            if __debug__:
                logger.error("Politic args not a list")
            args = []
        return (args, kwargs)

    def _extract_opt_msg(self, message):
        # TODO
        kwargs = {}
        args = []
        if not isinstance(kwargs, dict):
            if __debug__:
                logger.error("Msg kwargs not a dict")
            kwargs = {}
        if not isinstance(args, list):
            if __debug__:
                logger.error("Msg args not a list")
            args = []
        return (args, kwargs)

def configAWS():

    AWSenv = {
        'aws_shared_credentials_file': 'AWS_SHARED_CREDENTIALS_FILE',
        'aws_config_file': 'AWS_CONFIG_FILE',
        'aws_boto_config_file': 'BOTO_CONFIG',
    }

    configMapping = {
        'aws_profile': 'profile_name',
        'aws_region_name': 'region_name',
        'aws_session_token': 'aws_session_token',
        'aws_secret_access_key': 'aws_secret_access_key',
        'aws_access_key_id': 'aws_access_key_id',
    }

    AWSconfig = {
    }
    for key, val in AWSenv.items():
        if variables.config["dispatcher"][key] is not None and variables.config["dispatcher"][key] != '':
            os.environ[val]  = variables.config["dispatcher"][key]

    for key, val in configMapping.items():
        if variables.config["dispatcher"][key] is not None and variables.config["dispatcher"][key] != '':
            AWSconfig[val] = variables.config["dispatcher"][key]

    return AWSconfig


def launch(args, others):

    # Update conf
    arg = vars(args)
    update_conf(arg, "dispatcher")

    # Setup AWS
    variables.awsconfig = configAWS()

    # Initialise globals vars
    variables.MeteorAWS = EC2Meteor(KeyPairName=variables.config["dispatcher"]["keypair_name"], KeyPairFileName=variables.config["dispatcher"]["keypair_path"])

    # Create MiM from FrontEnd to Meteor.
    queue_saas_to_dispatch = RedisQueue([config.REDIS_QUEUE_NAME_SAAS_TO_DISPATCHER], variables.redis)
    queue_dispatch_to_meteor = RedisPriorityQueue([config.REDIS_QUEUE_NAME_DISPATCHER_TO_METEOR], variables.redis)
    FtoM = Dispatcher(queue_saas_to_dispatch, queue_dispatch_to_meteor,
                      'SimuLaunch', variables.config["dispatcher"]["default_simulation_launch_politic"])
    variables.actions_thread.append(FtoM)

    # Create MiM from Meteor to FrontEnd.
    queue_dispatch_to_saas = RedisQueue([config.REDIS_QUEUE_NAME_DISPATCHER_TO_SAAS], variables.redis)
    queue_meteor_to_dispatch = RedisQueue([config.REDIS_QUEUE_NAME_METEOR_TO_DISPATCHER], variables.redis)
    MtoF = Dispatcher(queue_meteor_to_dispatch, queue_dispatch_to_saas,
                      'ResultAvailable', variables.config["dispatcher"]["default_result_available_politic"])
    variables.actions_thread.append(MtoF)


def parser(parent_parser):
    parser = parent_parser.add_parser('dispatcher', help='dispatcher command help', aliases=['d', 'disp'])
    parser.add_argument('--default-simulation-launch-politic', type=str, default=None,
                        help='Default politics when a simulation-launch message comes to the DISPATCHER')
    parser.add_argument('--default-result-available-politic', type=str, default=None,
                        help='Default politics when a result-available message comes to the DISPATCHER')
    parser.add_argument('--keypair-name', type=str, default=None,
                        help='Name of the SSH KeyPair to communicate with MeteorServer')
    parser.add_argument('--keypair-path', type=str, default=None,
                        help='Path of the SSH KeyPair to communicate with MeteorServer')

    parser.add_argument('--aws-access-key-id', type=str, default=None,
                        help='AWS access key ID')

    parser.add_argument('--aws-secret-access-key', type=str, default=None,
                        help='AWS secret access key')

    parser.add_argument('--aws-session-token', type=str, default=None,
                        help='AWS session token')

    parser.add_argument('--aws-region-name', type=str, default=None,
                        help='AWS region name')

    parser.add_argument('--aws-profile', type=str, default=None,
                        help='AWS profile name')

    parser.add_argument('--aws-boto-config-file', type=str, default=None,
                        help='AWS boto config file')

    parser.add_argument('--aws-config-file', type=str, default=None,
                        help='AWS config file')

    parser.add_argument('--aws-shared-credentials-file', type=str, default=None,
                        help='AWS shared credentials file')
    
    parser.set_defaults(action=launch)
    return parser
