#!/usr/bin/env python3.5

import argparse
import signal
import sys

import Config.config as config
import Config.variables as variables

import pprint as pp

from Actions.Common import trait_common_args, parser as pcommon
from Actions.Dispatcher import parser as pd
from Actions.CronJobs import parser as pc



parser = argparse.ArgumentParser(prog='DISPATCHER')
pcommon(parser)

# Sub-parser section
subparsers = parser.add_subparsers(help='sub-command help')
# get Dispatcher sub command
pd(subparsers)

# get CronJobs sub command
pc(subparsers)


def wait():
    if __debug__:
        variables.logger.info("Waiting end of thread")
    for action in variables.actions_thread:
        action.join()


def run():
    if __debug__:
        variables.logger.info("Starting all threads")
    for action in variables.actions_thread:
        action.daemon = True
        action.start()


def signal_handler(signum, frame):
    if __debug__:
        variables.logger.info("Ask to stop by signal %d", signum)
    for action in variables.actions_thread:
        action.stop()
    wait()

# Set handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    """ DISPATCHER entry point. """
    # Remove prog name
    rest = sys.argv[1::]
    args = argparse.Namespace()
    common = False
    # Do all chaining sub command
    if not rest:
        describe(args, [])
        sys.exit(0)

    while rest:
        args, nrest = parser.parse_known_args(rest, namespace=args)
        if common and nrest == rest:
            break
        if not common:
            trait_common_args(args)
            common = True
        if rest and rest[0] == '--':
            # end of parsing, append rest to action
            args.action(args, rest[1::])
            break
        else:
            args.action(args, [])
        rest = nrest
    if len(variables.actions_thread) > 0:
        run()
        wait()

    sys.exit(0)
