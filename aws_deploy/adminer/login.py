

import pyotp
from rich.prompt import Prompt
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from aws_deploy.adminer.qrcode_generator import OtpQrCodeGenerator
from aws_deploy.cloudformation.parameter.db_password import DBPassword
from aws_deploy.cloudformation.template import CloudformationTemplate
from aws_deploy.config import (Config, ServiceTemplateNotFound, ServiceType,
                               console)
from aws_deploy.utils import db_host


class LoginAdminer:
    def __init__(self, short_name: str) -> None:
        self.driver = self._driver()
        self.template = CloudformationTemplate.from_short_name(short_name)
        self.config = Config()

    def _driver(self) -> webdriver.Chrome:
        return webdriver.Chrome(ChromeDriverManager().install())

    def fill_host(self):
        db_host_ele = self.driver.find_element(By.NAME, 'auth[server]')
        db_host_ele.clear()
        db_host_ele.send_keys(db_host())

    def fill_username(self):
        if self.template.service.Type == ServiceType.CORE:
            username = 'root'
        else:
            username = f'{self.template.service.Name}user'

        self.driver.find_element(By.ID, 'username').send_keys(username)

    def fill_password(self):
        param = DBPassword(self.template)
        ssm_param_name = param.ssm_param_name()

        fetched_param = param.ssm_stored.get_parameter(ssm_param_name)
        self.driver.find_element(By.NAME, 'auth[password]').send_keys(
            fetched_param['Value'])  # type: ignore

    def fill_otp(self):
        totp = pyotp.TOTP(OtpQrCodeGenerator().base32secret())
        self.driver.find_element(By.NAME, 'auth[otp]').send_keys(totp.now())

    def submit_form(self):
        self.driver.find_element(
            By.XPATH, '//*[@id="content"]/form/p/input').click()

    def login(self):
        # import subprocess
        # list_files = subprocess.run(["ssh", "ashraful@192.241.250.137",
        #                              "-p", "5151"], shell=True)

        # exit()
        try:
            service = self.config.find_service('adminer')
        except ServiceTemplateNotFound:
            console.log(
                "[red]Add adminer service in config/{}.yml[/red]".format(self.config.ENV))  # noqa: E501
            exit(1)
        self.driver.get(
            "https://{}".format(service.ServiceUrl))  # type: ignore
        self.fill_host()
        self.fill_username()
        self.fill_password()
        self.fill_otp()
        self.submit_form()

        while True:
            user_input = Prompt.ask('Type "done" and press Enter to exit...')
            if user_input.strip() == "done":
                break

        # driver.close()
