import click

from aws_deploy.aws_lambda.create_function import LambdaFunctionCreator
from aws_deploy.cli_common import common_params


@click.group(name="lambda")
def aws_lambda():
    "Create/Update Lambda Resource"
    pass


@aws_lambda.command()
@common_params
@click.argument("name")
def up(name: str):
    LambdaFunctionCreator(name).create()


# @aws_lambda.command
# def down():
#     print('lambda down')


# @click.group
# def check():
#     print("lambda check")


# @check.command
# def now():
#     print('now')


# aws_lambda.add_command(check)
