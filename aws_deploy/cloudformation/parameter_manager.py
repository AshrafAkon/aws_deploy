from typing import Iterable

from aws_deploy.cloudformation.parameter.resolver import ResolverFactory
from aws_deploy.cloudformation.template import CloudformationTemplate


class ParameterManager:
    def __init__(self,
                 template: CloudformationTemplate) -> None:
        self.template = template
        self.resolver_factory = ResolverFactory()

    def param_dict(self, key: str, value: str):
        return {
            'ParameterKey': key,
            'ParameterValue': value,
            'UsePreviousValue': False,
        }

    def resolved(self) -> Iterable:
        for name in self.template.parameters:
            factory = self.resolver_factory.get(name)

            if factory:
                resolver = factory(self.template)
                val = resolver.resolve(name)
                yield self.param_dict(name, val)
