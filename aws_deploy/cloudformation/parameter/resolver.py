from typing import Type

from . import db_password, general, ssm_stored
from .base import ParameterFactoryBase


# TODO: if service uses new domain then we need update alb certificate list
class NotDefined:
    def __init__(self) -> None:
        raise NotImplementedError


class ResolverFactory:
    _instance = None

    # def __new__(cls, *args, **kwargs):
    #     if not cls._instance:
    #         cls._instance = super().__new__(*args, **kwargs)
    #     return cls._instance

    _resolvers: dict[str, Type[ParameterFactoryBase]] = {
        'FullGithubRepositoryId': general.GeneralParameter,
        'ServiceUrl': general.GeneralParameter,
        'Branch': general.GeneralParameter,
        'DesiredCount': general.GeneralParameter,
        'ALBPriority': general.GeneralParameter,

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

    }

    def register(self, name: str, factory: Type[ParameterFactoryBase]):
        self._resolvers[name] = factory

    def resolvers(self):
        return self._resolvers

    def get(self, name: str):
        return self._resolvers.get(name)
