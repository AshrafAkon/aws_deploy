import boto3

from aws_deploy.cli_common import common_params
from aws_deploy.config import Config, console


def priority_list():
    client = boto3.client('elbv2')
    lbs = client.describe_load_balancers()
    lb_arn = ''
    for lb in lbs['LoadBalancers']:
        if lb['LoadBalancerName'] == f"{config.ENV}-ALB":
            lb_arn = lb['LoadBalancerArn']
            break
    listeners = client.describe_listeners(
        LoadBalancerArn=lb_arn)
    listener_arn = None
    for listener in listeners['Listeners']:
        if listener['Port'] == 443:
            listener_arn = listener['ListenerArn']
            break
    if listener_arn:
        rules = client.describe_rules(
            ListenerArn=listener_arn)
        for rule in rules['Rules']:
            if len(rule['Conditions']) > 0 and rule['Conditions'][0].get('HostHeaderConfig'):
                console.log(
                    f"{rule['Priority']} --> {rule['Conditions'][0]['HostHeaderConfig']['Values']}")
