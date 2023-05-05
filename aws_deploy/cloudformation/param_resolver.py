from typing import Iterable, Type

from aws_deploy.aws_lambda.params import LambdaRoleNameParameter
from aws_deploy.cloudformation.template import CloudformationTemplate
from aws_deploy.params import db_password, general, ssm_stored


# TODO: if service uses new domain then we need update alb certificate list
class NotDefined:
    def __init__(self) -> None:
        raise NotImplementedError


param_resolvers: dict[str, Type[general.ParameterResolver]] = {
    'FullGithubRepositoryId': general.GeneralParameter,
    'ServiceUrl': general.GeneralParameter,
    'Branch': general.GeneralParameter,
    'DesiredCount': general.GeneralParameter,
    'ALBPriority': general.GeneralParameter,

    # 'ThemeBranch': general.ThemeParameter,
    # 'ThemeGithubRepositoryId': general.ThemeParameter,

    'DBPassStore': db_password.DBPassword,
    'EnvironmentName': general.EnvironmentName,

    'CodestarConnectionArn': general.ConfigConstant,
    'Ec2DesiredCapacity': general.ConfigConstant,
    'DBInstanceClass': general.ConfigConstant,
    'LambdaPythonRuntime': general.ConfigConstant,
    'Ec2InstanceType': general.ConfigConstant,

    'ALBCertArn': general.AlbCertArn,

    'OtpSecretStore': ssm_stored.GeneratedSecret,
    'JwtStore': ssm_stored.GeneratedSecret,



    'Service': general.ServiceParameter,
    # 'CodebuildProjectName': general.CodebuildProjectNameParameter,

    'AllowedIp': general.AllowedIpParameter,
    'DbName': general.DbName,
    'DbUser': general.DBUserName,
    'ContainerEfsMountpoint': general.ConfigConstant,
    # 'GtmContainerConfigStore': NotDefined, #TODO: implement this

    'DotEnvStore': ssm_stored.UpdatableSSM,
    'HsApiKeyStore': ssm_stored.UpdatableSSM,
    'BcClientIdStore': ssm_stored.UpdatableSSM,
    'BcClientSecretStore': ssm_stored.UpdatableSSM,
    'ConfigStore': ssm_stored.UpdatableSSM,
    'AlgoliaAppIdStore': ssm_stored.UpdatableSSM,
    'AlgoliaWriteKeyStore': ssm_stored.UpdatableSSM,
    'IdevSshKeyStore': ssm_stored.UpdatableSSM,
    'AppKeyStore': ssm_stored.UpdatableSSM,
    'GhTokenStore': ssm_stored.UpdatableSSM,
    'SentryAuthTokenStore': ssm_stored.UpdatableSSM,

    # 'LambdaRoleName': LambdaRoleNameParameter,
}


class ParameterKeyNotFound(Exception):
    pass


class ParameterManager:
    def __init__(self,
                 template: CloudformationTemplate) -> None:
        self.template = template

    def param_dict(self, key: str, value: str):
        return {
            'ParameterKey': key,
            'ParameterValue': value,
            'UsePreviousValue': False,
        }

    def resolved(self) -> Iterable:
        for name in self.template.parameters:
            resolver_cls = param_resolvers.get(name)

            if resolver_cls:
                resolver = resolver_cls(self.template)
                val = resolver.resolve(name)
                yield self.param_dict(name, val)

    # def parse_params(self) -> List[Dict]:
    #     parsed_params = []
    #     for key in self.template.parameters:
    #         if key in param_resolvers:
    #             param = param_resolvers[key](self.template_name, key)
    #             param.add(parsed_params)
    #             param.update_body(self.template_yml)
    #     return parsed_params

    # def get_template_body(self) -> str:
    #     return dump_yaml(self.template_yml)
