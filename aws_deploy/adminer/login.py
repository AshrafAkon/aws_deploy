import os

import pyotp
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from aws_deploy.adminer.base import AdminerBase
from aws_deploy.adminer.qrcode_generator import OtpQrCodeGenerator
from aws_deploy.utils import db_host
from aws_deploy.config import Config, console
from aws_deploy.params.db_password import DBPassword


class LoginAdminer(AdminerBase):
    def __init__(self, service_name: str) -> None:
        self.driver = self._driver()
        self.service_name = service_name

    def _driver(self) -> webdriver.Chrome:

        driver_path = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'chromedriver')
        return webdriver.Chrome(ChromeDriverManager().install())

    def fill_host(self):
        db_host_ele = self.driver.find_element(By.NAME, 'auth[server]')
        db_host_ele.clear()
        db_host_ele.send_keys(db_host())

    def fill_username(self):
        username = 'root' if 'rds' in self.service_name else f'{self.service_name}user'
        self.driver.find_element(By.ID, 'username').send_keys(username)

    def fill_password(self):
        param = DBPasswordParameter(f'{self.service_name}-pipeline', '')
        fetched_param = param.get_parameter(param.ssm_param_name())
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
        self.driver.get(
            "https://{}".format(config.services['adminer-pipeline'].ServiceUrl))  # type: ignore
        self.fill_host()
        self.fill_username()
        self.fill_password()
        self.fill_otp()
        self.submit_form()

        while True:
            console.log('Type "done" and press Enter to exit...')
            if input() == "done":
                return
        # driver.close()
