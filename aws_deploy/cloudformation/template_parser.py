# from typing import Dict, List

# from cfn_tools import dump_yaml, load_yaml

# from aws_deploy.aws_lambda.params import LambdaRoleNameParameter
# from aws_deploy.cloudformation.template import CloudformationTemplate
# from aws_deploy.params import db_password, general, ssm_stored

# # TODO: if service uses new domain then we need update alb certificate list


# class ParameterKeyNotFound(Exception):
#     pass


# class ParameterValueResolver:
#     def __init__(self, template: CloudformationTemplate) -> None:
#         self._template = template

#     def parse_params(self) -> List[Dict]:
#         parsed_params = []
#         for param_key in self._template.parameters:
#             param_cls = param_resolvers.get(param_key)
#             if param_cls:

#                 param = param_cls(self._template, param_key)
#                 param.add(parsed_params)

#         return parsed_params

#     def get_template_body(self) -> str:
#         return dump_yaml(self.template_yml)
