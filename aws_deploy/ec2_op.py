import boto3
from mypy_boto3_ec2 import EC2Client

from aws_deploy.config import Config, console
from aws_deploy.params.general import AllowedIpParameter, ServiceParameter


class EcsEc2:
    def __init__(self) -> None:
        self._instances = None
        self.client: EC2Client = boto3.client('ec2')

    @property
    def instances(self):
        if not self._instances:
            resp = self.client.describe_instances(Filters=[{'Name': 'tag:deployment',
                                                            'Values': [config.ENV]},
                                                           {
                'Name': 'instance-state-name',
                'Values': ['running']
            }])
            # type:ignore
            self._instances = []
            for group in resp['Reservations']:
                self._instances.extend(group['Instances'])
        return self._instances

    def ec2_ips(self):
        for ec2 in self.instances:
            console.log(ec2['PublicIpAddress'])  # type: ignore

    def ec2_ip(self, service_name: str | None = None) -> str:  # type: ignore
        if not service_name:
            return self.instances[0]['PublicIpAddress']
        cluster = f'{config.ENV}-ec2'
        client = boto3.client('ecs')
        task_arn = client.list_tasks(
            cluster=cluster,
            serviceName=service_name+"-pipeline",

        )['taskArns'][0]
        tasks = client.describe_tasks(
            cluster=cluster, tasks=[task_arn])['tasks']
        container_instance_arn = tasks[0]['containerInstanceArn']
        con_instance = client.describe_container_instances(cluster=cluster,

                                                           containerInstances=[
                                                               container_instance_arn]
                                                           )['containerInstances'][0]
        ec2_instance_id = con_instance['ec2InstanceId']
        for ec2 in self.instances:
            if ec2['InstanceId'] == ec2_instance_id:
                return ec2['PublicIpAddress']

    def ssh_login(self, service_name: str | None = None):

        ec2_ip = self.ec2_ip(service_name)
        console.log(ec2_ip)
        sg_id = self.sg_id(ec2_ip)
        inbound_rules = self.inbound_rules(sg_id)
        self.verify_sg_ingress(sg_id, inbound_rules)
        command = f"ssh ec2-user@{ec2_ip} -v"

        from applescript import tell
        tell.app('Terminal', 'do script "' + command + '"')

    def sg_id(self, instance_ip: str):
        for ec2 in self.instances:
            if ec2['PublicIpAddress'] == instance_ip:
                return ec2['SecurityGroups'][0]['GroupId']
        return self.instances[0]['SecurityGroups'][0]['GroupId']

    def inbound_rules(self, sg_id: str):
        response = self.client.describe_security_group_rules(
            Filters=[
                {
                    'Name': 'group-id',
                    'Values': [
                        sg_id
                    ]
                },
            ],
            # SecurityGroupRuleIds=[
            #     'string',
            # ],
            DryRun=False,
            # NextToken='string',
            MaxResults=123
        )
        return [sg_rule for sg_rule in response['SecurityGroupRules']
                if sg_rule['IsEgress'] == False]  # type: ignore

    def verify_sg_ingress(self, sg_id: str, inbound_rules: list):
        # pyright: reportTypedDictNotRequiredAccess=false

        updatable_rule = None
        for sg_rule in inbound_rules:
            if sg_rule['FromPort'] == 22 and sg_rule['ToPort']:
                updatable_rule = sg_rule
                break
        current_ip = AllowedIpParameter.value()
        if updatable_rule and updatable_rule['CidrIpv4'] != current_ip:
            allowed_params = ['IpProtocol', 'FromPort', 'ToPort',
                              'CidrIpv4', 'CidrIpv6', 'PrefixListId', 'ReferencedGroupId']
            rule_id = updatable_rule['SecurityGroupRuleId']

            updatable_rule = {_key: _val for _key,
                              _val in updatable_rule.items() if _key in allowed_params}

            updatable_rule['CidrIpv4'] = current_ip  # type: ignore
            # updatable_rule['ReferencedGroupId'] = self.sg_id
            sg_rules_list = [{'SecurityGroupRuleId': rule_id,
                              'SecurityGroupRule': updatable_rule
                              }
                             ]
            response = self.client.modify_security_group_rules(
                GroupId=sg_id,
                SecurityGroupRules=sg_rules_list)  # type: ignore
            # response
