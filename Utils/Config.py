import ast
import Config.variables as variables

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


def update_conf(cmdline, section):
    if __debug__:
        logger.debug("Configure section %s", section)
    for var in variables.config[section]:
        if __debug__:
            logger.debug("Trying to load parameter %s", var)
        try:
            conf = variables.configfile[section]
        except KeyError:
            if __debug__:
                logger.debug("section %s not in config file %s", section)
            conf = None
        if var in cmdline and cmdline[var] is not None:
            if __debug__:
                logger.debug("param in commandline: %s", cmdline[var])
            ret = cmdline[var]
        elif conf is not None and var in conf:
            ret = ast.literal_eval(conf[var])
        else:
            continue
        if ret is not None and not isinstance(ret, type(variables.config[section][var])):
            if __debug__:
                logger.warning("type of param %s differ : (default) %s / (input) %s. Not changing value",
                               var,  type(variables.config[section][var]), type(ret))
            pass
        else:
            variables.config[section][var] = ret
