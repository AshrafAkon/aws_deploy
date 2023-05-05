import enum
import os
from dataclasses import dataclass, field
from typing import Optional

import rich.traceback
import yaml
from rich.console import Console

rich.traceback.install()
console = Console()


Profile = 'aalp-prod'  # aws profile set with aws-cli
name_prefix = "infra"
DEPLOY_ENV = "dev"
TAG_ENV = "env"


# the order of the template core_templates_map is very important.
# As each core template depends on the previous resource.
class DeploymentEnv(enum.Enum):
    DEV = 'dev'
    PROD = 'prod'


class ServiceType(enum.Enum):
    CORE = 'core'
    SERVICE = 'service'
    LAMBDA = 'lambda'


@dataclass
class ServiceConfig:
    Name: str
    ShortName: str
    Type: ServiceType
    DesiredCount: Optional[int] = 2
    FullGithubRepositoryId: Optional[str] = None
    Branch: Optional[str] = None
    ALBPriority: Optional[str] = None
    ServiceUrl: Optional[str] = None


class ServiceTemplateNotFound(Exception):
    pass


class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


@dataclass
class Config(metaclass=Singleton):
    """A singleton that stores all service related config

    Loads config/dev.yml by default. Prod is loaded with --prod flag
    """

    CodestarConnectionArn: str = ''
    DBInstanceClass: str = ''
    services: list[ServiceConfig] = field(default_factory=list)
    Ec2DesiredCapacity: int = 1
    Ec2InstanceType: str = 't3.small'
    ContainerEfsMountpoint: str = '/home/ec2-user/efsdata'

    _instance = None

    ENV = DEPLOY_ENV
    TAG_ENV = TAG_ENV
    REGION = 'us-east-1'
    NO_WAIT: bool = False
    CONFIG_DIR = 'config'
    lambda_python_version = "python:3.9"
    LambdaPythonRuntime = lambda_python_version.replace(":", '')
    waiter_config = {
        'Delay': 10,
        'MaxAttempts': 120
    }

    lambda_dir = "lambda_code"

    # backup_templates_map = {
    #     'backup_efs': 'backup_efs'
    # }
    @staticmethod
    def yml_config(yml_path: str):
        with open(yml_path, "r") as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as exc:
                console.log("[red]Error in config file[/red]")
                console.log(exc)
                exit()

    def find_service(self, short_name: str) -> ServiceConfig:
        for service in self.services:
            if service.ShortName == short_name or service.Name == short_name:
                return service

        raise ServiceTemplateNotFound

    @classmethod
    def from_env(cls, env: DeploymentEnv):

        # open(os.path.join(pathlib.Path(__file__).parent.resolve()
        # current directory should have config folder
        config_path = os.path.join(cls.CONFIG_DIR, f"{env.value}.yml")
        yml_config = cls.yml_config(config_path)
        body_keys = [
            'CodestarConnectionArn',
            'DBInstanceClass',
            'Ec2DesiredCapacity',
            'Ec2InstanceType',
            'ContainerEfsMountpoint'

        ]
        _attrs = {key: val for key, val in yml_config.items()
                  if key in body_keys}

        _attrs['services'] = []
        for service_type in ServiceType:
            for name, service in yml_config[service_type.value].items():
                if not service:
                    service = {}
                if not service.get('ShortName'):
                    service['ShortName'] = name.split("-")[0]
                service['Type'] = service_type
                service['Name'] = name
                _attrs['services'].append(ServiceConfig(**service))

        return cls(**_attrs)
