from abc import ABC, abstractmethod

from aws_deploy.cloudformation.template import CloudformationTemplate


class ParameterFactoryBase(ABC):

    def __init__(self, template: CloudformationTemplate):
        """_summary_

        Args:
            template (CloudformationTemplate): _description_
        """
        self.template = template

    @abstractmethod
    def resolve(self, parameter_name: str):
        """
        Resolve the parameter value.
        """
        raise NotImplementedError
