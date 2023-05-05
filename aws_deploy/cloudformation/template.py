import os
from dataclasses import dataclass
from typing import Optional

from cfn_tools import dump_yaml, load_yaml

from aws_deploy.config import Config, ServiceConfig

# from aws_deploy.config import Config

STACK_FAILED_STATUS_LIST = [
    'CREATE_FAILED',
    'ROLLBACK_COMPLETE',
    'DELETE_FAILED',
    'UPDATE_FAILED',
    'UPDATE_ROLLBACK_FAILED',
    'ROLLBACK_FAILED'
    # 'UPDATE_ROLLBACK_COMPLETE'
]


@dataclass
class CloudformationTemplate:
    content: dict
    service: ServiceConfig

    @property
    def parameters(self) -> dict:
        return self.content['Parameters']

    @classmethod
    def from_short_name(cls, short_name: str,
                        service_dir: Optional[str] = None):
        config = Config()
        service = config.find_service(short_name)
        if service_dir is None:
            template_path = os.path.join(
                service.Type.value, f"{service.Name}.yml")
        else:
            template_path = os.path.join(service_dir, f"{service.Name}.yml")
        with open(template_path) as f:
            template_body = f.read()
        _content: dict = load_yaml(template_body)
        # TODO: handle keyerror

        return cls(
            _content,
            service,
        )

    def add_resource(self, name: str, definition: dict):
        self.content[name] = definition

    def __str__(self) -> str:
        return dump_yaml(self.content)
