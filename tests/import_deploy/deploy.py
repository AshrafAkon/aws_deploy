# class BcalgoliaSyncVpcConfig(VpcConfig):
#     def sg_ids(self):

#         response = self.cf.describe_stacks(
#             StackName=f'{self.config.ENV}-core-alb-external')
#         outputs = response["Stacks"][0]["Outputs"]  # type: ignore

#         return [output['OutputValue']  # type:ignore
#                 for output in outputs \
#                 if 'ALBPublicSG' in output['OutputKey']]  # type:ignore


from aws_deploy.cloudformation.parameter import ssm_stored
from aws_deploy.cloudformation.parameter.resolver import ResolverFactory

resolver = ResolverFactory()

resolver.register('testTokeStore', ssm_stored.UpdatableSSM)
