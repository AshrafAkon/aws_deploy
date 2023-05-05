import boto3
from mypy_boto3_cloudformation import CloudFormationClient

from aws_deploy.config import Config, ServiceType, console


def full_stack_name(t_type: ServiceType, t_name: str):
    return f"{Config().ENV}-{t_type.value}-{t_name}"


def db_host():
    cf_client: CloudFormationClient = boto3.client(
        'cloudformation')  # type: ignore
    response = cf_client.describe_stacks(
        StackName=f"{Config().ENV}-core-rds")
    outputs = response["Stacks"][0]["Outputs"]  # type: ignore
    for output in outputs:
        keyName = output["OutputKey"]  # type: ignore
        if keyName == 'RDSEndpointAddress':
            console.log(output["OutputValue"])  # type: ignore
            return output["OutputValue"]   # type: ignore
    exit()
