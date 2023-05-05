from abc import ABC, abstractmethod
from typing import Type

import boto3
from mypy_boto3_cloudformation import CloudFormationClient
from mypy_boto3_ecr import ECRClient

from aws_deploy.utils import full_stack_name
from aws_deploy.config import Config, console

deletable_stack_statuses = [
    'CREATE_FAILED',
    'CREATE_COMPLETE',
    'ROLLBACK_COMPLETE',
    'DELETE_FAILED',
    'UPDATE_COMPLETE',
    'UPDATE_FAILED',
    'UPDATE_ROLLBACK_FAILED',
    'UPDATE_ROLLBACK_COMPLETE'
]


class ResourceDeleter(ABC):
    def __init__(self, resource: dict) -> None:
        self.resource = resource

    @abstractmethod
    def resource_client(self):
        raise NotImplementedError

    def deleted(self):
        return self.resource['ResourceStatus'] == 'DELETE_COMPLETE'

    @abstractmethod
    def delete(self):
        raise NotImplementedError


class S3BucketDeleter(ResourceDeleter):

    def resource_client(self):

        # this is a s3 bucket.
        # we cant delete a s3 bucket without removing all objects
        # from it. So force deleting it

        return boto3.resource('s3')

    def should_delete(self):

        return Config().ENV != 'prod' \
            and self.resource['ResourceStatus'] != 'DELETE_COMPLETE'

    def delete(self):
        if not self.should_delete():
            return
        console.log(
            "[red]Deleting Stack resource =>{} [/red]"
            .format(self.resource['PhysicalResourceId']))

        client = self.resource_client()
        bucket = client.Bucket(
            self.resource['PhysicalResourceId'])  # type: ignore

        bucket.objects.all().delete()


class ECRRepositoryDeleter(ResourceDeleter):
    def __init__(self, resource: dict) -> None:
        super().__init__(resource)
        self.client: ECRClient = boto3.client('ecr')

    def deleted(self):

        try:
            self.client.describe_repositories(
                repositoryNames=[
                    self.resource['PhysicalResourceId']

                ],
            )
        except self.client.exceptions.RepositoryNotFoundException:
            return True
        return False
        # return self.resource['ResourceStatus'] == 'DELETE_COMPLETE'

    def delete_resource(self):
        if self.deleted():
            return
        console.log(
            "[red]Deleting Stack resource => {}[/red]"
            .format(self.resource['PhysicalResourceId']))
        # this is a ecr repository. So we need to delete all images
        # that is uploaded to this repository. Otherwise we cant delete
        # this
        self.client.delete_repository(
            repositoryName=self.resource['PhysicalResourceId'], force=True)


delete_resource_map: dict[str, Type[ResourceDeleter]] = {
    'AWS::ECR::Repository': ECRRepositoryDeleter,
    'AWS::S3::Bucket': S3BucketDeleter
}


class StackDeleter:
    def __init__(self, short_name: str) -> None:
        self.cf: CloudFormationClient = boto3.client('cloudformation')
        self.config = Config()
        self.name = full_stack_name

    def list_stacks(self):
        return self.cf.list_stacks(
            StackStatusFilter=deletable_stack_statuses)['StackSummaries']  # type: ignore # noqa: E501

    @staticmethod
    def get_all_resources(env):
        # TODO: add more concrete resource tagging
        return boto3.client('resourcegroupstaggingapi')\
            .get_resources(TagFilters=[
                {
                    'Key': 'env',
                    'Values': [
                        env,
                    ]
                },
            ], ResourceTypeFilters=[
                'cloudformation',
            ], )

    @staticmethod
    def show_deletable_stacks(full_names: list):
        console.log("The following stacks will be deleted",
                    style="bold white on red", justify="center")
        console.log("\n")

        for name in full_names:
            console.log(
                f":green_square: {name}", emoji=True)
        console.log("\n")

    @staticmethod
    def confirm_operation():
        console.log("""Are you sure about deleting the above stacks?
        Type the word 'confirm' to proceed""",
                    style="bold white on grey39", justify="left")
        if input() != "confirm":
            console.log("Cancelled. No stacks deleted.",
                        style="green")
            exit()

    def delete_stack_resources(self, stack_name: str):
        try:
            resources = self.cf.list_stack_resources(StackName=stack_name)
        except self.cf.exceptions.ClientError:
            console.log(f'stack resources doesnt exist for {stack_name}')
            return

        for resource in resources['StackResourceSummaries']:
            # print(resource)
            # if resource['LogicalResourceId'] in stack['Stacks'][0]['StackStatusReason']: # noqa: E501
            # this resource is the reason of delete being failed
            deleter_cls = delete_resource_map.get(resource['ResourceType'])
            if deleter_cls:
                deleter_cls(resource).delete()  # type: ignore

    def delete(self, stack_name: str):
        console.log(
            f"[red]Deleting stack: [deep_sky_blue3]{stack_name}[/deep_sky_blue3][/red]")  # noqa: E501
        # console.log(
        #     f"[green]Stack last status: [deep_sky_blue3]{stack_name}[/deep_sky_blue3] [/green] ") # noqa: E501
        self.delete_stack_resources(stack_name)
        self.cf.delete_stack(StackName=stack_name)
        if not self.config.NO_WAIT:
            waiter = self.cf.get_waiter('stack_delete_complete')
            waiter.wait(StackName=stack_name,
                        WaiterConfig=self.config.waiter_config)  # type: ignore

            console.log("[green]Stack deleted.[/green]")

# TODO: complete delete all stacks


# class DeleteAllStack(DeleteStackOperation):
#     def stack_full_name_list(self) -> list[str]:
#         full_names = []
#         for template_name in config.core_templates_map.values():
#             full_names.append(full_stack_name('core', template_name))
#         for template_name in config.service_templates_map.values():
#             full_names.append(full_stack_name('service', template_name))
#         return full_names

#     def run(self):
#         # stacks = self.list_stacks()
#         # resources = self.get_all_resources(config.ENV)
#         # deletable_stacks = self.filter_deletable_stacks(stacks, resources)
#         full_names = self.stack_full_name_list()
#         full_names.reverse()
#         self.show_deletable_stacks(full_names)
#         self.confirm_operation()
#         for full_name in full_names:
#             self.delete_stack(full_name)
#             break
#         console.log('All Cloudformation Stacks Deleted')


# class DeleteAllServiceStacks(DeleteStackOperation):
#     def run(self):
#         for template_name in config.service_templates_map.values():
#             self.delete_stack(full_stack_name('service', template_name))

# TODO: complete delete service stacks
# class DeleteSingleStack(DeleteStackOperation):

#     def run(self):
#         stack_name = full_stack_name(
#             self.template_type, self.t_name)
#         self.show_deletable_stacks([stack_name])
#         self.confirm_operation()
#         self.delete_stack(stack_name)
