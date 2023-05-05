import click

from aws_deploy.adminer.login import LoginAdminer
from aws_deploy.adminer.qrcode_generator import OtpQrCodeGenerator
from aws_deploy.cli_common import common_params
from aws_deploy.config import Config


@click.group(name="adminer")
def adminer():
    """Adminer login and otp generation"""
    pass


@adminer.command()
@common_params
def gen_qr():
    OtpQrCodeGenerator().generate()


@adminer.command()
@common_params
@click.argument("service")
def login(service):
    LoginAdminer(service).login()
