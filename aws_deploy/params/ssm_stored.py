
import base64
import secrets

import boto3
from mypy_boto3_ssm import SSMClient

from aws_deploy.cloudformation.template import CloudformationTemplate
from aws_deploy.config import Config, console
from aws_deploy.params.general import ParameterResolver

# r5aFR0s6_OsqGdSrwbJjv2ub-sq3xS2KNBF_iA


class SSMStored:
    def __init__(self):
        self.client: SSMClient = boto3.client('ssm')
        self.secret_length = 28
        self._sec_token = None
        # self.config = Config()
        # self.secret_token = secrets.token_urlsafe(self.secret_length)

    @property
    def secret_token(self):
        if not self._sec_token:
            self._sec_token = secrets.token_urlsafe(self.secret_length)
        return self._sec_token

    @secret_token.setter
    def secret_token(self, val: str):
        self._sec_token = val

    def put_parameter(self, ssm_param_name: str, tags=None,
                      data_type='text', overwrite=False):
        # default encryption key used fora ssm parameter
        if tags is None:
            tags = []
        return self.client.put_parameter(
            Name=ssm_param_name,
            Description='string',
            Value=self.secret_token,
            Type='SecureString',
            # KeyId='string',
            Overwrite=overwrite,
            # AllowedPattern='string',
            Tags=tags,
            Tier='Standard',
            # Policies='string',
            DataType=data_type,

        )

    # def ssm_param_name(self, param_name: str):
    #     return f"{Config().ENV}-{self.template.name}-{param_name}"

    def get_parameter(self, ssm_param_name: str):
        return self.client.get_parameter(
            Name=ssm_param_name, WithDecryption=True).get('Parameter')

    # def resolve(self, param_name: str):
    #     ssm_param_name = self.ssm_param_name(param_name)
    #     try:
    #         fetched_param = self.get_parameter(ssm_param_name)
    #     except self.client.exceptions.ParameterNotFound:
    #         fetched_param = self.put_parameter(ssm_param_name)
    #     self.version = fetched_param.get('Version')
    #     return ssm_param_name


class UpdatableSSM(ParameterResolver):
    def __init__(self, template: CloudformationTemplate):
        self.ssm_stored = SSMStored()
        self.ssm_stored.secret_token = 'replace-this-with-key'
        super().__init__(template)

    @property
    def secret_token(self):
        return 'replace-this-with-key'

    def ask_user(self, param_name: str):
        console.log('ssm name: {}'.format(param_name))
        console.log(f'Provide {param_name} on the browser window ')
        import webbrowser

        webbrowser.open(
            'https://us-east-1.console.aws.amazon.com/systems-manager/parameters/{}/description?region=us-east-1'.format(param_name))  # noqa: E501
        while True:
            console.log(
                '[green]Type "done" and press enter when done[/green]')
            if input() == "done":
                break

    def resolve(self, param_name: str):

        param_name = "{}-{}-{}".format(Config().ENV,
                                       self.template.service.Name,
                                       param_name)

        # self.secret_token = f'replace-this-with-{param_name}-key'
        try:
            self.ssm_stored.get_parameter(param_name)
        except self.ssm_stored.client.exceptions.ParameterNotFound:
            self.ssm_stored.put_parameter(param_name)
            self.ask_user(param_name)

        return param_name


# class GtmContainerConfigStore(UpdatableSSMParameterName):
#     def ssm_param_name(self, param_name: str) -> str:
#         return f"{Config().ENV}-{param_name}"


class GeneratedSecret(ParameterResolver):
    def __init__(self, template: CloudformationTemplate):
        self.ssm_stored = SSMStored()
        self.ssm_stored.secret_token = self.secret_token()
        super().__init__(template)

    def secret_token(self):
        """Returns base64 encoded secret.

        Adminer otp needs base64 encoded string

        Returns:
            str: base64 encoded secret string
        """
        secret_str = secrets.token_urlsafe(60).encode('ascii')
        return base64.b64encode(secret_str).decode("ascii")

    def ssm_param_name(self, param_name: str):
        return f"{Config().ENV}-{self.template.service.Name}-{param_name}"

    def resolve(self, param_name: str):
        ssm_param_name = self.ssm_param_name(param_name)
        try:
            fetched_param = self.ssm_stored.get_parameter(ssm_param_name)
        except self.ssm_stored.client.exceptions.ParameterNotFound:
            fetched_param = self.ssm_stored.put_parameter(ssm_param_name)
        self.version = fetched_param.get('Version')
        return ssm_param_name
