import Config.config as config
defaultconfig = {
    'common': {
        'pidfile': '/var/run/launcher.pid',
        'loglevel': 0,
        'logconfigfile': '/etc/launcher/logger.conf',
        'redis_host': config.REDIS_HOST,
        'redis_port': config.REDIS_PORT,
    },
    'dispatcher': {
        'default_simulation_launch_politic': 'Default.Default',
        'default_result_available_politic': "Default.Default",
        'keypair_name': "DISPATCHER",
        'keypair_path': '',
        'aws_access_key_id': '',
        'aws_secret_access_key': '',
        'aws_session_token': '',
        'aws_region_name': '',
        'aws_profile': '',
        'aws_boto_config_file': '',
        'aws_config_file': '',
        'aws_shared_credentials_file': '',
    }
}
