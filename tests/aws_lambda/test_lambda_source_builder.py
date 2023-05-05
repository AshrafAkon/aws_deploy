import io
import os
import zipfile

import docker
import pytest

from aws_deploy.aws_lambda.source_builder import SourceBuilder

# from aws_deploy.cloudformation.template import CloudformationTemplate
# from aws_deploy.config import Config


# Mock a CloudformationTemplate object
class MockCloudformationTemplate:
    class MockService:
        Name = "test_service"

    service = MockService()


# Mock a Config object


class MockConfig:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lambda_dir = os.path.join(script_dir, "example_lambda_code")
    lambda_python_version = "python:3.9"


@pytest.fixture
def lambda_builder():
    template = MockCloudformationTemplate()
    config = MockConfig()
    return SourceBuilder(template, config)  # type: ignore


def test_build_creates_runnable_zip(lambda_builder: SourceBuilder, tmp_path):
    zip_content = lambda_builder.build()

    # Extract the contents of the ZIP file to a temporary directory
    zip_file = zipfile.ZipFile(io.BytesIO(zip_content), "r")
    zip_file.extractall(tmp_path)

    client = docker.from_env()

    # Run the main.py script in the Lambda Docker container
    container = client.containers.run(
        image='public.ecr.aws/lambda/{}'.format(
            lambda_builder.config.lambda_python_version),
        command="python index.py",
        entrypoint="",
        volumes={str(tmp_path): {'bind': '/var/task', 'mode': 'ro'}},
        detach=True,
        tty=True

    )

    container.wait()  # type:ignore
    # Check if the container exit code is 0, indicating success
    exit_code = container.attrs['State']['ExitCode']  # type: ignore
    assert exit_code == 0

    # Get the container logs
    container_logs = container.logs(  # type: ignore
        stdout=True, stderr=True).decode('utf-8')

    # Check if the logs contain the expected output
    assert "This domain is for use" in container_logs
