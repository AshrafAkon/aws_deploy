import os
import enum
from abc import abstractmethod
from dataclasses import dataclass

import boto3
from mypy_boto3_cloudformation import Client as CloudformationClient

from aws_deploy.config import Config


class TemplateType(enum.Enum):
    core = 'core'
    service = 'service'
    aws_lambda = 'lambda'


@dataclass
class CloudformationTemplate:
    name: str
    body: str
    parameters: dict
    parameter_values: dict
    template_type: TemplateType

    @classmethod
    def from_short_name(cls, short_name: str):
        t_name = ''
        t_type = TemplateType.service
        f_path = os.path.join(
            t_type.value, t_name + ".yml")


class CloudformationStack:
    def __init__(self, template: CloudformationTemplate) -> None:
        self.cf = boto3.client('cloudformation', region_name=config.Region)
        self.template: CloudformationTemplate = template

    # def get_full_name(self, short_name: str, t_type: str):
    #     try:
    #         if t_type == 'core':
    #             return config.core_templates_map[short_name]
    #         # elif t_type == 'backup':
    #         #     return config.backup_templates_map[short_name]
    #         else:
    #             return config.service_templates_map[short_name]
    #     except KeyError:
    #         raise TemplateNotFoundException('Template shortname not found.')
    @abstractmethod
    def run(self):
        raise NotImplementedError()


class StackTemplateFileFoundException(Exception):
    pass


class _StackModifyOperation(CloudformationStack):
    def describe_stack(self, stack_name):
        try:
            return self.cf.describe_stacks(StackName=stack_name)
        except Exception as e:
            # console.log(e)
            return None

    # def full_stack_name(self, t_type: str, t_name: str):
    #     return f"{config.ENV}-{t_type}-{t_name}"

    def find_template_type(self, short_name):
        # if short_name in config. backup_templates_map.keys():
        #     return "backup"
        if short_name in config.core_templates_map.keys():
            return 'core'

        return 'service'

    @abstractmethod
    def run(self):
        raise NotImplementedError()


class StackModifySingleOperation(StackModifyOperation):
    def __init__(self, short_name: str) -> None:
        super().__init__()
        self.short_name = short_name
        self.template_type = self.find_template_type(short_name)
        self.t_name = self.gen_template_name(
            short_name, self.template_type)
