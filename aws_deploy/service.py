import enum

import boto3


class Services(enum.Enum):
    cloudformation = 'cloudformation'


class ServiceContainer:
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state
        if not hasattr(self, '_services'):
            self._services = {}

    def register(self, service_name: Services, service):
        self._services[service_name] = service

    def get(self, service_name: Services):
        if service_name not in self._services:
            raise ValueError(f"Service {service_name} not registered")
        return self._services[service_name]


def register_default():
    cf = boto3.client(Services.cloudformation.value)
    ServiceContainer().register(Services.cloudformation, cf)


# Register the default CloudFormation service
register_default()
