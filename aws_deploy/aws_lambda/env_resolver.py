from typing import Callable

from aws_deploy.cloudformation.template import CloudformationTemplate


class EnvResolverNotDefined(Exception):
    pass


class LambdaEnvVarResolver:
    resolvers = {}

    def resolve(self, template: CloudformationTemplate):
        if self.resolvers.get(template.service.Name):
            return {'Variables':
                    self.resolvers[template.service.Name](template)}
        raise EnvResolverNotDefined

    @classmethod
    def register(cls, func: Callable):
        cls.resolvers[func.__name__.replace("_", "-")] = func
        return None


class LambdaVpcConfig:
    resolvers = {}

    def resolve(self, template: CloudformationTemplate):
        if self.resolvers.get(template.service.Name):
            return {'Variables':
                    self.resolvers[template.service.Name](template)}
        raise EnvResolverNotDefined

    @classmethod
    def register(cls, func: Callable):
        cls.resolvers[func.__name__.replace("_", "-")] = func
