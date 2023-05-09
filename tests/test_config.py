import os
import shutil
import tempfile
from unittest.mock import patch

import pytest
import yaml

from aws_deploy.config import Config, DeploymentEnv, ServiceConfig, ServiceType

# Update the path to your config files if necessary
config_dir = "config"


def test_load_correct_yml_file():
    # Reset the singleton instance before each test
    Config._instance = None

    dev_config = Config.from_env(DeploymentEnv.DEV)

    # Reset the singleton instance before each test
    Config._instance = None

    prod_config = Config.from_env(DeploymentEnv.PROD)

    with open(os.path.join(config_dir, "dev.yml"), "r") as f:
        dev_yml = yaml.safe_load(f)

    with open(os.path.join(config_dir, "prod.yml"), "r") as f:
        prod_yml = yaml.safe_load(f)

    assert dev_config.CodestarConnectionArn == dev_yml['CodestarConnectionArn']
    assert (prod_config.CodestarConnectionArn ==
            prod_yml['CodestarConnectionArn'])


def test_core_service_loading():
    # Reset the singleton instance before each test
    Config._instance = None

    config = Config.from_env(DeploymentEnv.DEV)

    core_services = [
        service for service in config.services
        if service.Type == ServiceType.CORE]
    service_services = [
        service for service in config.services
        if service.Type == ServiceType.SERVICE]

    assert len(core_services) > 0
    assert len(service_services) > 0


def test_service_config_optional_values():
    core_service = ServiceConfig(
        Name="core-example",
        ShortName="core",
        Type=ServiceType.CORE,
    )

    service_service = ServiceConfig(
        Name="service-example",
        ShortName="service",
        Type=ServiceType.SERVICE,
        FullGithubRepositoryId="example/repo",
        Branch="main",
        ALBPriority="100",
        ServiceUrl="https://example.com",
    )

    assert core_service.Name == "core-example"
    assert core_service.ShortName == "core"
    assert core_service.Type == ServiceType.CORE
    assert core_service.DesiredCount == 2
    assert core_service.FullGithubRepositoryId is None
    assert core_service.Branch is None
    assert core_service.ALBPriority is None
    assert core_service.ServiceUrl is None

    assert service_service.Name == "service-example"
    assert service_service.ShortName == "service"
    assert service_service.Type == ServiceType.SERVICE
    assert service_service.DesiredCount == 2
    assert service_service.FullGithubRepositoryId == "example/repo"
    assert service_service.Branch == "main"
    assert service_service.ALBPriority == "100"
    assert service_service.ServiceUrl == "https://example.com"


@pytest.fixture(autouse=True)
def run_before_every_test():
    Config._instance = None


def test_optional_values_from_config_file():
    # Create temporary config directory
    temp_config_dir = tempfile.mkdtemp()
    temp_config_path = os.path.join(
        temp_config_dir, f"{DeploymentEnv.DEV}.yml")

    with open(temp_config_path, "w") as temp_config_file:
        temp_config_file.write("""
CodestarConnectionArn: "arn:aws:codestar:example"
DBInstanceClass: "db.t3.micro"
core:
  core-example:
    ShortName: core
lambda:
  rds-opeartion:
service:
  service-example:
    ShortName: service
    FullGithubRepositoryId: example/repo
    Branch: main
    ALBPriority: 100
    ServiceUrl: https://example.com
""")

    with patch("aws_deploy.config.Config.CONFIG_DIR", new=temp_config_dir):
        config = Config.from_env(DeploymentEnv.DEV)

    core_service = config.find_service("core")
    service_service = config.find_service("service")

    # Clean up temporary config directory
    shutil.rmtree(temp_config_dir)

    assert core_service.Name == "core-example"
    assert core_service.ShortName == "core"
    assert core_service.Type == ServiceType.CORE
    assert core_service.DesiredCount == 2
    assert core_service.FullGithubRepositoryId is None
    assert core_service.Branch is None
    assert core_service.ALBPriority is None
    assert core_service.ServiceUrl is None

    assert service_service.Name == "service-example"
    assert service_service.ShortName == "service"
    assert service_service.Type == ServiceType.SERVICE
    assert service_service.DesiredCount == 2
    assert service_service.FullGithubRepositoryId == "example/repo"
    assert service_service.Branch == "main"
    assert service_service.ALBPriority == 100
    assert service_service.ServiceUrl == "https://example.com"
