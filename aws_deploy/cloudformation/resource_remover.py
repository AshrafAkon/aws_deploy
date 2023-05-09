from abc import ABC, abstractmethod

import boto3
from mypy_boto3_ecr import ECRClient

from aws_deploy.config import Config, console


class ResourceRemover(ABC):
    def __init__(self, resource: dict) -> None:
        self.resource = resource

    def deleted(self):
        return self.resource['ResourceStatus'] == 'DELETE_COMPLETE'

    @abstractmethod
    def delete(self):
        raise NotImplementedError


class S3BucketRemover(ResourceRemover):

    def should_delete(self):

        return Config().ENV != 'prod' \
            and self.resource['ResourceStatus'] != 'DELETE_COMPLETE'

    def delete(self):
        if not self.should_delete():
            return
        console.log(
            "[red]Deleting Stack resource =>{} [/red]"
            .format(self.resource['PhysicalResourceId']))

        client = boto3.resource('s3')
        bucket = client.Bucket(
            self.resource['PhysicalResourceId'])  # type: ignore

        bucket.objects.all().delete()


class ECRRepositoryRemover(ResourceRemover):
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
