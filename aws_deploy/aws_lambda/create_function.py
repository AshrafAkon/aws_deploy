import os
from abc import abstractmethod

import boto3
from mypy_boto3_lambda import LambdaClient

from aws_deploy.aws_lambda.env_resolver import LambdaEnvVarResolver
# from aws_deploy.aws_lambda.params import LambdaRoleNameParameter
from aws_deploy.aws_lambda.source_builder import SourceBuilder
from aws_deploy.cloudformation.stack_creator import StackCreator
from aws_deploy.config import Config, console
from aws_deploy.params.general import ParameterResolver


class RdsMasterPasswordSSMNameParameter(ParameterResolver):
    # FIXME
    pass


class CreateLambdaStack(StackCreator):
    def __init__(self, short_name: str) -> None:
        super().__init__(short_name)

    def template_f_path(self):
        return os.path.join('lambda', f'{self.template.service.ShortName}.yml')

    # def gen_template_name(self, short_name: str, t_type: str):
    #     return config.ENV + "-"+short_name


class LambdaOperation:
    def __init__(self) -> None:
        self.client = boto3.client('lambda')

    @abstractmethod
    def run(self):
        raise NotImplementedError


class LambdaFunctionCreator:
    def __init__(self, short_name: str, config: Config | None = None) -> None:
        self.stack_creator = StackCreator(short_name)
        self.config = config if config else Config()
        self.function_name = f"{self.config.ENV}-{self.stack_creator.template.service.Name}"  # noqa: E501
        self.service_name = self.stack_creator.template.service.Name
        self.build_dir = os.path.join(
            self.config.lambda_dir, 'build',
            self.service_name)
        self.zip_f_path = os.path.join(
            self.config.lambda_dir, 'build',
            self.service_name)

        self.builder = SourceBuilder(self.stack_creator.template)
        self.client: LambdaClient = boto3.client('lambda')  # type: ignore

    def lambda_env(self):
        resolver = LambdaEnvVarResolver()
        return resolver.resolve(self.stack_creator.template)

    def lambda_function_exists(self):
        try:
            self.client.get_function(FunctionName=self.function_name)
        except self.client.exceptions.ResourceNotFoundException:
            return False
        return True

    def function_arn(self):
        stack = self.stack_creator.get_stack()
        assert stack and stack.Outputs
        for output in stack.Outputs:
            if output.OutputKey == 'LambdaArn':
                return output.OutputValue
        raise ValueError('LabmdaArn not found in stack outputs.')

    def update_function_code(self):
        resp = self.client.update_function_code(
            FunctionName=self.function_arn(),
            ZipFile=self.builder.build())
        console.log(resp)

    def wait_for_status_change(self):
        console.log('Getting waiter for lambda')
        waiter = self.client.get_waiter('function_updated')
        try:
            waiter.wait(FunctionName=self.function_name)
        except Exception:
            console.log('Lambda is not in desired state')

    def last_status(self):
        response = self.client.get_function(
            FunctionName=self.function_name
        )
        return response['Configuration']['LastUpdateStatus']  # type: ignore

    def update_function(self):
        self.update_function_code()
        self.wait_for_status_change()
        console.log(self.last_status())
        # self.update_function_configaration()
        console.log("Lambda Function updated")

    def create(self):
        self.stack_creator.create()
        self.update_function()
