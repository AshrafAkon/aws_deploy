import functools
from typing import Callable

import click

from aws_deploy.config import Config, DeploymentEnv, console

# from click import core


def common_params(func: Callable):
    @click.option('--prod', is_flag=True, default=False, help="executes on production")  # noqa: E501
    @click.option('--no-wait', is_flag=True, default=False, help="Wait for status update to complete")  # noqa: E501
    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        if kwargs.get('prod') is True:
            env = DeploymentEnv.PROD
        else:
            env = DeploymentEnv.DEV
        config = Config.from_env(env)
        # if kwargs.get('no_wait') is True:
        config.NO_WAIT = kwargs.pop('no_wait', False)

        for key in ['prod', 'no_wait']:
            kwargs.pop(key, None)

        console.log(f'Current env: [green]{config.ENV}[/green]')
        # config.load_services()
        return func(*args, **kwargs)
    return wrapper
