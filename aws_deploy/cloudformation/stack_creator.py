import boto3
from botocore import exceptions
from mypy_boto3_cloudformation import CloudFormationClient

from aws_deploy.cloudformation.param_resolver import ParameterManager
from aws_deploy.cloudformation.stack import (STACK_FAILED_STATUS_LIST,
                                             CloudformationStack)
# from aws_deploy.cloudformation.stack_deleter import StackDeleter
from aws_deploy.cloudformation.template import CloudformationTemplate
from aws_deploy.config import Config, console
from aws_deploy.utils import full_stack_name

# def permitted_on(env: str):

#     def gate_decorator(func: Callable):
#         if config.ENV != env:
#             console.log(
#                 f'{func.__name__} is not permitted in {config.ENV}
# environment.')

#         def wrapper(*args, **kargs):
#             func(*args, **kargs)
#         return wrapper

#     return gate_decorator


class StackCreator:
    # def __init__(self, short_name: str) -> None:
    #     self.waiter_status = None
    #     super().__init__(short_name)
    def __init__(self, short_name: str) -> None:
        self.config = Config()
        self.cf: CloudFormationClient = boto3.client(
            'cloudformation', region_name=self.config.REGION)
        self.template = CloudformationTemplate.from_short_name(short_name)
        self.stack_name = full_stack_name(
            self.template.service.Type,
            self.template.service.Name)

    # @permitted_on('dev')

    def delete_stack(self, stack_name: str):
        # FIXME
        pass
        # if self.config.ENV == "prod":
        #     console.log('Wont delete stack in prod')
        #     exit()
        # console.log(
        #     "Deleting stack because it was failed last time.")
        # delete_op = DeleteStackOperation()
        # delete_op.delete_stack(stack_name)

    def _wait_for(self, waiter_status: str):
        console.log(
            "[green]Waiting for {} [/green]".format(waiter_status))

        waiter = self.cf.get_waiter(
            waiter_name=waiter_status)  # type: ignore
        waiter.wait(StackName=self.stack_name,
                    WaiterConfig=self.config.waiter_config)
        console.log("[green]Done.[/green]")

    def stack_tags(self, stack_name: str):
        return [

            {
                'Key': 'deployment',
                'Value': self.config.ENV
            },
            {
                'Key': 'stack',
                'Value': stack_name
            }
        ]

    def stack_capabilities(self):
        return [
            'CAPABILITY_IAM',
            'CAPABILITY_NAMED_IAM'
        ]

    def update_stack(self, params) -> bool:
        try:
            self.cf.update_stack(**params)

        except exceptions.ClientError as e:
            if e.response.get('Error'):
                error_message = e.response['Error']['Message']  # type: ignore
                if error_message == 'No updates are to be performed.':
                    console.log(
                        "[green]No new update on {}[/green]"
                        .format(self.template.service.Name))
                    return False

            raise e
        return True

    def create_stack_params(self, stack_name: str):
        # self.find_template_type(self.short_name)

        # template_f_path = self.template_f_path()

        resolver = ParameterManager(self.template)
        content_str = str(self.template)
        self.cf.validate_template(TemplateBody=content_str)
        return {'StackName': stack_name,
                'TemplateBody': content_str,
                'Capabilities': self.stack_capabilities(),
                'Parameters': list(resolver.resolved()),
                'Tags': self.stack_tags(stack_name)}

    def _stack_updating(self, stack):
        try:
            return stack['Stacks'][0]['StackStatus'] == 'UPDATE_IN_PROGRESS'
        except TypeError:
            return False

    def get_stack(self) -> CloudformationStack | None:
        try:
            resp = self.cf.describe_stacks(StackName=self.stack_name)

            # type: ignore

            return CloudformationStack.from_dict(  # type : ignore
                resp['Stacks'][0])  # type : ignore
        except Exception as e:
            console.log(e)
            return None

    def _stack_failed(self, stack):
        return stack['Stacks'][0]['StackStatus'] in STACK_FAILED_STATUS_LIST

    def create(self):

        stack = self.get_stack()

        if stack:
            if stack.failed():
                self.delete_stack(self.stack_name)
                stack = None
            elif stack.updating():
                console.log(
                    f'Previous update in progress for: {self.template.service.Name}')  # noqa: E501
                return
        params = self.create_stack_params(self.stack_name)
        waiter_status = None
        if not stack:
            console.log(
                f"[green]Creating Stack {self.template.service.Name}[/green]")
            self.cf.create_stack(**params)
            waiter_status = 'stack_create_complete'
        else:
            console.log(
                f"[green]Updating Stack {self.template.service.Name}[/green]")
            if self.update_stack(params):
                waiter_status = 'stack_update_complete'

        if waiter_status and not self.config.NO_WAIT:
            self._wait_for(waiter_status)

# TODO: migrate all core stack creation
# class CreateCoreStacks(StackOperation):
#     def run(self):
#         for short_name in config.core_templates_map:
#             op = CreateStack(short_name)
#             op.run()

# TODO: Migrate create all service stacks
# class CreateAllServices(StackOperation):
#     def run(self):
#         for short_name, full_name in config.service_templates_map.items():
#             if full_name in config.services.keys():
#                 console.log(full_name)

#                 op = CreateStack(short_name)
#                 op.run()
#                 console.log("[blue] == == == == == == == ==[/blue]")
