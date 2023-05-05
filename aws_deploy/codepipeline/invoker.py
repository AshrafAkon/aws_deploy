from typing import Literal
from aws_deploy.utils import full_stack_name

import boto3


class CodePipelineInvoker:
    def __init__(self, stack_name: str):

        self.stack_name = stack_name

    def get_pipeline_details(self):
        # Get the ARN of the CodePipeline from the CloudFormation stack
        client = boto3.client('cloudformation')
        response = client.describe_stacks(StackName=self.stack_name)
        stack_outputs = response['Stacks'][0]['Outputs']  # type: ignore
        pipeline_arn = None
        for output in stack_outputs:
            if output['OutputKey'] == 'PipelineArn':  # type: ignore
                pipeline_arn = output['OutputValue']  # type: ignore
                break

        # Get the details of the CodePipeline
        if pipeline_arn:
            client = boto3.client('codepipeline')
            response = client.get_pipeline_state(
                name=pipeline_arn.split('/')[-1])
            return response
        else:
            return None

    def invoke_pipeline(self):
        # Invoke the CodePipeline
        pipeline_details = self.get_pipeline_details()
        if pipeline_details:
            name: Literal['codepipeline'] = 'codepipeline'
            client = boto3.client(name)
            response = client.start_pipeline_execution(
                name=pipeline_details['pipelineName'])
            return response
        else:
            return None
    
    def run(self, short_name: str):
        full_stack_name(
           'service', short_name)
