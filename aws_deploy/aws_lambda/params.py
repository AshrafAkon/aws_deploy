from aws_deploy.config import Config, console
from aws_deploy.params.general import ParameterResolver


class LambdaRoleNameParameter(ParameterResolver):

    def reolve(self):
        return f"{config.ENV}-{self.t_name}-role"
