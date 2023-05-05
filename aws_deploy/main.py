import importlib
import logging
import os

import click

from aws_deploy.adminer.commands import adminer
from aws_deploy.alb import priority_list
from aws_deploy.aws_lambda.commands import aws_lambda
from aws_deploy.cli_common import common_params
from aws_deploy.cloudformation.stack_creator import StackCreator
from aws_deploy.cloudformation.stack_deleter import StackDeleter
from aws_deploy.config import Config, DeploymentEnv

log = logging.getLogger('deploy.cf.create_or_update')

failed_stack_statuses = [
    'CREATE_FAILED',
    'ROLLBACK_COMPLETE',
    'DELETE_FAILED',
    'UPDATE_FAILED',
    'UPDATE_ROLLBACK_FAILED',
    'ROLLBACK_FAILED'
    # 'UPDATE_ROLLBACK_COMPLETE'
]
deploy_module_name = "deploy"


class StdCommand(click.core.Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params.insert(0, click.core.Option(
            ('--env',), help='Override env'))


def import_deploy():
    try:
        importlib.import_module(
            deploy_module_name, package=None)

    except (ImportError, AttributeError) as e:
        click.echo(f"Failed to load or execute deploy module: {e}")


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option('--prod', is_flag=True, default=False, help="Executes on production")  # noqa: E501
@click.option('--no-wait', is_flag=True, default=False, help="Wait for status update to complete")  # noqa: E501
@click.pass_context
def cli(ctx: click.core.Context, prod: bool, no_wait: bool):
    ctx.ensure_object(dict)
    # env = DeploymentEnv.PROD if prod else DeploymentEnv.DEV

    # ctx.obj = Config.from_env(env)

    import_deploy()
# @click.group
# def signal_cf():
#     import boto3
#     client = boto3.client('cloudformation')
#     response = client.signal_resource(
#         StackName='string',
#         LogicalResourceId='string',
#         UniqueId='string',
#         Status='SUCCESS'
#     )


@cli.command()
@common_params
@click.option("-s", "--service-name", help="Full template name without .yml extension")  # noqa: E501
def delete_stack(service_name: str):
    StackDeleter(service_name).delete()


@cli.command()
@common_params
@click.option("--services", is_flag=True, default=False, help="Deletes all service stacks")  # noqa: E501
@click.option("--doit", is_flag=True, default=False, help="Delete all stacks in configured env")  # noqa: E501
def delete_stacks(services, doit):

    if not doit:
        return
    if services:
        DeleteAllServiceStacks().run()


@cli.command()
@common_params
@click.argument("name")
@click.option("--recreate", is_flag=True,  default=False, help="Deletes old stack and creates new one")  # noqa: E501
def create(name: str, recreate: bool):
    if recreate:
        DeleteSingleStack(name).run()
    StackCreator(name).create()


# @cli.command(cls=StdCommand)
# @common_params
# # @cli.command()
# @click.option("-c", "--core", is_flag=True, help="For creating core infrastructure")  # noqa: E501
# @click.option("-s", "--services", is_flag=True, help="For creating all available services")  # noqa: E501
# def create_stacks(**kargs):
#     os.environ['LAMBDA_INVOKE'] = "YES"
#     if kargs['core']:
#         CreateCoreStacks().run()
#     elif kargs['all_services']:
#         CreateAllServices().run()


@cli.command()
@common_params
def env():
    pass


# @cli.command()
# @common_params

# def lambda_up(name):
#     CreateLambdaFunction(name).run()


cli.add_command(adminer)
cli.add_command(aws_lambda)
cli.command(priority_list)

if __name__ == '__main__':
    cli()
