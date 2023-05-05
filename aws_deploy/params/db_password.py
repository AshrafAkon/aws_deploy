import base64
import json
import time

import boto3
from mypy_boto3_lambda import LambdaClient

from aws_deploy.cloudformation.template import CloudformationTemplate
from aws_deploy.config import Config, console
from aws_deploy.params.general import DbName, DBUserName, ParameterResolver
from aws_deploy.params.ssm_stored import SSMStored


class DBPassword(ParameterResolver):
    def __init__(self, template: CloudformationTemplate):
        super().__init__(template)
        self.ssm_stored = SSMStored()

    def ssm_param_name(self) -> str:
        return f"{Config().ENV}-rds-{self.unique_name()}-password"

    def unique_name(self) -> str:
        if "rds" in self.template.service.Name.lower():
            # rds stack template. So this is root password
            return "master"
        return self.template.service.Name

    def create_db_user(self, param_name: str):
        """Creates rds user using lambda function

        Args:
            param_name (str): Cloudformation Stack Parameter name
        """
        lambda_client: LambdaClient = boto3.client('lambda')  # type: ignore
        user_name = DBUserName(
            self.template).resolve(param_name)
        db_name = DbName(
            self.template).resolve(param_name)

        # lambda function uses this dict to call internal function
        args = {'USER_NAME': user_name,
                'USER_PASS': self.ssm_stored.secret_token,
                'DB_NAME': db_name}
        root_pass = self.ssm_stored.get_parameter(
            f"{Config().ENV}-rds-master-password"
        )['Value']  # type: ignore
        func_name = f"{Config().ENV}-rds-operation"
        payload = json.dumps({'ROOT_PASS': root_pass,  # type: ignore
                              'ARGS': args,
                              'OPERATION': 'create'})
        while True:

            try:
                resp = lambda_client.invoke(
                    LogType='Tail',
                    FunctionName=func_name,
                    Payload=payload
                )
                break
            except lambda_client.exceptions.ResourceNotReadyException:
                console.log(
                    '{}-rds_operation lambda function not ready yet. '.format(Config().ENV))  # noqa: E501
                time.sleep(5)
        console.log('Lambda Execution Logs: ')
        console.log(base64.b64decode(
            resp['LogResult']).decode("utf-8"))  # type: ignore
        assert (resp.get('FunctionError') is None)

    def resolve(self, param_name: str):
        """Returns aws ssm parameter name

        Creates the ssm parameter if it doesnt exist. A random password is
        generated when ssm parameter is created.

        Args:
            param_name (str): _description_

        Returns:
            _type_: _description_
        """

        ssm_param_name = self.ssm_param_name()
        try:
            self.ssm_stored.get_parameter(ssm_param_name)
        except self.ssm_stored.client.exceptions.ParameterNotFound:
            self.ssm_stored.put_parameter(ssm_param_name)

            # version = fetched_param.get('Version')
            self.create_db_user(param_name)
        return ssm_param_name
