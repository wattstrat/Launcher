#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-

if __debug__:
    import logging
    import logging.config
"""
Global settings file for DISPATCHER
All basics settings are specified here.
"""

# SaaS <=> Dispatcher
REDIS_QUEUE_NAME_SAAS_TO_DISPATCHER = 'saas_to_dispatcher'
REDIS_QUEUE_NAME_DISPATCHER_TO_SAAS = 'dispatcher_to_saas'

# Dispatcher <=> Main Simulation Queue
REDIS_QUEUE_NAME_DISPATCHER_TO_METEOR = 'dispatcher_to_meteor'
REDIS_QUEUE_NAME_METEOR_TO_DISPATCHER = 'meteor_to_dispatcher'

# ConJobs PriorityQueue
REDIS_QUEUE_NAME_CRONJOBS = 'CronJobs'

# ==== LOGGING CONFIG ====
LOGCONF_FILENAME = 'logger.conf'
# == END LOGGING CONFIG ==

REDIS_HOST = ''
REDIS_PORT = 6379

__ACTIONS__ = ["Dispatcher", "MongoCleaner", "PostponedActions"]
__DEFAULT_ACTION__ = "Dispatcher"

POLITIC_ALIAS = {
}
ALLOWED_POLITICS = {
    'SimuLaunch': [
        'Dispatcher.Politics.SimuLaunch.Default',
        'Dispatcher.Politics.SimuLaunch.Default.Default',
        'Dispatcher.Politics.SimuLaunch.OnePerSimu',
        'Dispatcher.Politics.SimuLaunch.OnePerSimu.OnePerSimu',
        'Dispatcher.Politics.SimuLaunch.OnlyOnePerSimu',
        'Dispatcher.Politics.SimuLaunch.OnlyOnePerSimu.OnlyOnePerSimu',
        'Dispatcher.Politics.SimuLaunch.SplitByYear',
        'Dispatcher.Politics.SimuLaunch.SplitByYear.SplitByYear',

    ],
    'ResultAvailable': [
        'Dispatcher.Politics.ResultAvailable.Default',
        'Dispatcher.Politics.ResultAvailable.Default.Default',
        'Dispatcher.Politics.ResultAvailable.DestroyAfterNoSimuRunning',
        'Dispatcher.Politics.ResultAvailable.DestroyAfterNoSimuRunning.DestroyAfterNoSimuRunning',
        'Dispatcher.Politics.ResultAvailable.DestroyAfterSimuWithinHour',
        'Dispatcher.Politics.ResultAvailable.DestroyAfterSimuWithinHour.DestroyAfterSimuWithinHour'

    ],
}

CRONJOBS_ALIAS = {
}
ALLOWED_CRONJOBS = [
]

DEFAULT_REDIS_TIME = 1

__DEFAULT_HANDLER_CLASS__ = {
    'SimuLaunch': 'Dispatcher.Politics.SimuLaunch.Default.Default',
    'ResultAvailable': 'Dispatcher.Politics.ResultAvailable.Default.Default',
}

# Subscription <=> Instance

instance_from_subscription = {
    'subscription1': 't2.micro',
    'subscription2': 't2.mega',
    'default': 't2.nano'
}

__IMAGE_ID__ = 'ami-'
__SECURITY_GROUP__ = ['meteor-prod']

__METEOR_IMAGE_ID__ = 'ami-'
__METEOR_SECURITY_GROUP__ = ['meteor-prod']


__SMTP_LOGIN__ = ''
__SMTP_PASSWORD__ = ''
__SMTP_SERVER__ = ''


__DEFAULT_KEYPAIR_NAME__ = 'DISPATCHER'
__SSH_USERNAME__ = 'user'
__SSH_PORT__ = 22

version = "0.5"
