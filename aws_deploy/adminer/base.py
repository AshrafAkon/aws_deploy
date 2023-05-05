import boto3
from aws_deploy.utils import db_host
from mypy_boto3_ssm import SSMClient


class AdminerBase:
    def __init__(self) -> None:
        self.client: SSMClient = boto3.client('ssm')

    def get_parameter(self, parameter_name):
        return self.client.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        ).get('Parameter')
