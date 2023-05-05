import fnmatch
import re
from abc import ABC, abstractmethod

import boto3
import requests

from aws_deploy.cloudformation.template import CloudformationTemplate
from aws_deploy.config import Config, console


class ParameterResolver(ABC):

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


# class Parameter:
#     """Base class of all template parameter
#     """

#     def __init__(self, template: CloudformationTemplate, parameter_key: str):
#         """_summary_

#         Args:
#             template (CloudformationTemplate): _description_
#             parameter_key (str): _description_
#         """
#         self.template = template
#         self.p_key = parameter_key

#     def param_dict(self, param_value: str):
#         return {
#             'ParameterKey': self.p_key,
#             'ParameterValue': param_value,
#             'UsePreviousValue': False,
#         }

#     def add_job(self, jobs: list):
#         pass

#     def value(self):
#         raise NotImplementedError

#     def add(self, params: list):
#         """Adds formatted parameter dict to supplied params list

#         Args:
#             params (list): current parameter list
#         """
#         params.append(self.param_dict(self.value()))

#     def update_body(self, template):
#         """Updated template body if needed. Example: cert arn

#         Args:
#             template (_type_): _description_
#         """
#         pass


class ServiceNotFound(Exception):
    pass


class GeneralParameter(ParameterResolver):

    def resolve(self, param_name: str):
        return str(getattr(self.template.service, param_name))


class AllowedIpParameter(ParameterResolver):
    @staticmethod
    def is_valid_ip(ip: str):
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def resolve(self, param_name: str):

        response = requests.get("http://checkip.amazonaws.com")
        ip = response.text.strip()
        console.log('Current public ip: {}'.format(ip))
        if self.is_valid_ip(ip):
            return f"{ip}/32"
        raise Exception(
            '''Couldnt Find valid public id address.
            Check your internet connection''')  # type: ignore


class ServiceParameter(ParameterResolver):
    def resolve(self, param_name: str):
        return self.template.service.Name


# class CodebuildProjectNameParameter(TemplateParameter):
#     def value(self):
#         return f"{config.ENV}-{self.t_name}-codebuild"


class EnvironmentName(ParameterResolver):
    def resolve(self, param_key: str):
        return Config().ENV


# class CodeStarConnectionArnParameter(TemplateParameter):
#     def value(self):
#         return config.CODESTAR_CONNECTION_ARN


class ConfigConstant(ParameterResolver):
    def resolve(self, param_key: str):
        return getattr(Config(), param_key)


class AlbCertArn(ParameterResolver):
    def __init__(self, template: CloudformationTemplate):
        self.cert_arns = list()
        self.config = Config()
        super().__init__(template)

    @staticmethod
    def certs():
        """Returns aws acm CertificateSummaryList

        :return: List of CertificateSummary
        :rtype: list
        """
        client = boto3.client('acm')  # type: ignore
        return client.list_certificates()['CertificateSummaryList']

    def url_in_use(self, cert: dict, domains: list) -> bool:
        if fnmatch.filter(domains, cert['DomainName']):
            return True

        for alt_name in cert['SubjectAlternativeNameSummaries']:
            if fnmatch.filter(domains, alt_name):  # type: ignore
                return True
        return False

    def service_domains(self) -> list:
        return [service.ServiceUrl
                for service in self.config.services if service.ServiceUrl]

    def get_allowed_cert_arns(self):
        """Returns the list of certificate arns that should be added to alb

        :return: List of aws acm resource ARN
        :rtype: list
        """

        service_domains = self.service_domains()
        for cert in self.certs():
            if self.url_in_use(cert, service_domains):
                self.cert_arns.append(cert['CertificateArn'])

    def listener_extra_cert_resource(self) -> dict:
        certs = [{"CertificateArn": cert} for cert in self.cert_arns]
        return {
            "Type": "AWS::ElasticLoadBalancingV2::ListenerCertificate",
            "Properties": {
                "Certificates": certs,
                "ListenerArn": {'Ref': 'PublicLoadBalancerHTTPSListener'}
            }
        }

    def resolve(self, param_name: str):
        if not len(self.cert_arns):
            # No more certs available for this alb
            return
        main_cert_arn = self.cert_arns.pop(0)
        listener_cert = self.listener_extra_cert_resource()
        self.template.add_resource('ALBExtraCerts', listener_cert)
        return main_cert_arn


class DbName(ParameterResolver):
    def resolve(self, param_name: str):
        name = re.sub('[^A-Za-z0-9]+', '', self.template.name.lower())
        return name.replace("pipeline", "")


class DBUserName(DbName):
    def resolve(self, param_name: str):
        return f"{super().resolve(param_name)}user"
