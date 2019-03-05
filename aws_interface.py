import boto3
import botocore
import time
import paramiko
import socket
import datetime

from io import StringIO

from mail import MeteorCreateEmail
from threading import RLock

import Config.config as config
import Config.variables as variables

if __debug__:
    import logging
    logger = logging.getLogger(__name__)

pay_step = datetime.timedelta(hours=1)


class EC2(object):

    def __init__(self, DryRun=False, 
                 ImageId=config.__IMAGE_ID__, SecurityGroup=config.__SECURITY_GROUP__,
                 KeyPairName=None, KeyPairFileName=None, KeyPairFileNamePass=None, Filters=[],
                 **kwargs):
        self._lock = RLock()
        self._ressource = boto3.resource('ec2', **variables.awsconfig)
        self._client = boto3.client('ec2', **variables.awsconfig)
        self._DryRun = DryRun
        self._ImageId = ImageId
        self._SecurityGroup = SecurityGroup.copy()
        self._filters = Filters.copy()

        if KeyPairName is None:
            KeyPairName = config.__DEFAULT_KEYPAIR_NAME__
        try:
            # Key already created?
            self._keypair = self._ressource.KeyPair(KeyPairName)
            self._keypair.load()
            if KeyPairFileName is None:
                raise KeyError("KeyPairFileName must be provide")
            self._rsakey = paramiko.RSAKey(filename=KeyPairFileName, password=KeyPairFileNamePass)
        except botocore.exceptions.ClientError:
            # TODO: must fine-grained raise filter
            # No key found
            keypair = self._client.create_key_pair(KeyName=KeyPairName)
            if __debug__:
                logger.info("KeyPair %s created ; \n%s", KeyPairName, keypair["KeyMaterial"])
            self._keypair = self._ressource.KeyPair(KeyPairName)
            self._keypair.load()
            self._rsakey = paramiko.RSAKey(file_obj=StringIO(keypair["KeyMaterial"]))
            if KeyPairFileName is not None:
                # Save the key
                self._rsakey = paramiko.write_private_key_file(KeyPairFileName, password=KeyPairFileNamePass)

    def number_instance(self):
        # returns the number of instances with the given status
        response = self._client.describe_instance_status(
            DryRun=self._DryRun, Filters=self._filters)
        return len(response['InstanceStatuses'])

    def create(self, InstanceType, MinCount, MaxCount):
        if __debug__:
            logger.info("Launching (%d / %d) instance '%s'", MinCount, MaxCount, InstanceType)
        ret = self._ressource.create_instances(
            DryRun=self._DryRun, InstanceType=InstanceType, MinCount=MinCount,
            MaxCount=MaxCount, ImageId=self._ImageId, SecurityGroups=self._SecurityGroup, KeyName=self._keypair.name)
        return ret

    def destroy(self, id_instance):
        with self._lock:
            instance = self.get_instance(id_instance)
            try:
                instance.terminate(DryRun=self._DryRun)
            except botocore.exceptions.ClientError as e:
                if __debug__:
                    logger.debug("Error when processing terminate instance %s : '%s'", id_instance, e)
                raise e

    def get_next_to_stop(self):
        instances = self.get_instances()
        deltas = {id_inst: (datetime.datetime.now(datetime.timezone.utc) - inst.launch_time) % pay_step
                  for (id_inst, inst) in instances.items()}
        for inst, delt in deltas.items():
            if __debug__:
                logger.debug("Instance %s : time consumed since pay %s", inst, delt)
        max_inst = max(deltas, key=lambda k: deltas[k])
        return max_inst, instances[max_inst]

    def stop_best(self):
        with self._lock:
            inst_id, inst = self.get_next_to_stop()
            try:
                inst.terminate(DryRun=self._DryRun)
            except botocore.exceptions.ClientError as e:
                if __debug__:
                    logger.debug("Error when processing terminate instance %s : '%s'", inst_id, e)
                raise e

    def get_instances(self):
        # return running instance
        filters = self._filters.copy()
        filters.append({'Name': "instance-state-name", 'Values': ['running']})
        instances = self._ressource.instances.filter(DryRun=self._DryRun, Filters=filters)
        return {inst.id: inst for inst in instances}

    def get_pending_instances(self):
        # return running instance
        filters = self._filters.copy()
        filters.append({'Name': "instance-state-name", 'Values': ['pending']})
        instances = self._ressource.instances.filter(DryRun=self._DryRun, Filters=filters)
        return {inst.id: inst for inst in instances}

    def get_instance(self, id_instance):
        instances = self.get_instances()
        if id_instance not in instances.keys():
            raise KeyError("Instance not in managed instance")
        return instances[id_instance]

    def exec_on(self, id_instance, cmd, connect_intra=True):
        # TODO BETTER ALL
        instance = self.get_instance(id_instance)

        if connect_intra:
            ip = instance.private_ip_address
        else:
            ip = instance.public_ip_address
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, config.__SSH_PORT__))

        t = paramiko.Transport(sock)
        try:
            t.start_client()
        except paramiko.SSHException:
            if __debug__:
                logger.error('*** SSH negotiation failed to %s.', id_instance)
            return None
        t.auth_publickey(config.__SSH_USERNAME__, self._rsakey)
        if not t.is_authenticated():
            if __debug__:
                logger.error('*** Authentication failed. :( for %s.', id_instance)
            return None

        chan = t.open_session()
        out = b""
        out_stderr = b""

        chan.exec_command(cmd)
        while not chan.exit_status_ready():
            while chan.recv_ready() or chan.recv_stderr_ready():
                if chan.recv_ready():
                    out = out + chan.recv(1000)
                if chan.recv_stderr_ready():
                    out_stderr = out_stderr + chan.recv_stderr(1000)
        while chan.recv_ready() or chan.recv_stderr_ready():
            if chan.recv_ready():
                out = out + chan.recv(1000)
            if chan.recv_stderr_ready():
                out_stderr = out_stderr + chan.recv_stderr(1000)

        ret = chan.recv_exit_status()
        if __debug__:
            logger.info('Command return %d / %s / %s', ret, out, out_stderr)
        t.close()
        return (ret, out, out_stderr)


class EC2Meteor(EC2):

    def __init__(self, **kwargs):
        kwargs["ImageId"] = config.__METEOR_IMAGE_ID__
        kwargs["SecurityGroup"] = config.__METEOR_SECURITY_GROUP__
        if "Filters" in kwargs:
            kwargs["Filters"].append({'Name': "tag:ServerType", 'Values': ['Meteor']})
        else:
            kwargs["Filters"] = [{'Name': "tag:ServerType", 'Values': ['Meteor']}]
        EC2.__init__(self, **kwargs)
        self._mail = MeteorCreateEmail()

    def create(self, InstanceType, MinCount, MaxCount):
        # launches ec2 instances with METEOR image attached
        instances = EC2.create(self, InstanceType, MinCount, MaxCount)
        for instance in instances:
            instance.create_tags(DryRun=self._DryRun, Tags=[{'Key': 'ServerType', 'Value': 'Meteor'}])
        self._mail.send(instances_id=[x.id for x in instances], instances_type=InstanceType)
        return instances
