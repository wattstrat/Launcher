import smtplib
import Config.config as config
from email.message import EmailMessage
from email.headerregistry import Address

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class Email(object):

    def __init__(self,
                 smtpserver=config.__SMTP_SERVER__,
                 login=config.__SMTP_LOGIN__, password=config.__SMTP_PASSWORD__):
        self._login = login
        self._password = password
        self._smtpserver = smtpserver

    def send_text(self, fromaddr, toaddrs, msg):
        try:
            with smtplib.SMTP(self._smtpserver, 587) as server:
                server.starttls()
                server.ehlo()
                server.login(self._login, self._password)
                if __debug__:
                    logger.debug("Send mail to %s from %s : '%s'", toaddrs, fromaddr, msg)
                server.sendmail(fromaddr, toaddrs, msg)
                server.quit()
        except smtplib.SMTPAuthenticationError as e:
            if __debug__:
                logger.error("Error in smtp authentification: '%s'", e)

    def send(self, msg):
        try:
            with smtplib.SMTP(self._smtpserver, 587) as server:
                server.starttls()
                server.ehlo()
                server.login(self._login, self._password)
                if __debug__:
                    logger.debug("Send mail '%s'", msg)
                server.send_message(msg)
                server.quit()
        except smtplib.SMTPAuthenticationError as e:
            if __debug__:
                logger.error("Error in smtp authentification: '%s'", e)


class MeteorEmail(Email):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._msg = EmailMessage()
        # TODO : change to variable
        self._msg['From'] = "do-not-reply@server"
        self._msg['To'] = "admin"

    def _update(self, *args, **kwargs):
        raise NotImplemented("_update should be implemented")

    def send(self, *args, **kwargs):
        self._update(*args, **kwargs)
        print(self._msg)
        Email.send(self, self._msg)


class MeteorStatsEmail(MeteorEmail):

    def _update(self, *args, **kwargs):
        self._msg['Subject'] = "Stats on Meteor Instance"
        instances_stats = kwargs.get("instances_stats", {})
        simulations = kwargs.get("simulations", 0)
        ids_msg = ["⎈ IDs : {inst_id!s} running during {running_time!s} in actual state {state!s} ({tags!s})".format(
            inst_id=inst_id, **stats)
            for inst_id, stats in instances_stats.items()]
        self._msg.set_content("{:d} instances on AWS for {} simulations \n{!s}\n".format(
            len(ids_msg), simulations, "\n".join(ids_msg))
        )


class MeteorCreateEmail(MeteorEmail):

    def _update(self, *args, **kwargs):
        instances_id = kwargs.get("instances_id", [])
        instances_type = kwargs.get("instances_type", "")
        self._msg.set_content("{:d} instances '{}' launched.\nIDs : {!s}\n".format(
            len(instances_id), instances_type, instances_id)
        )
