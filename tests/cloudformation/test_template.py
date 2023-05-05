import os

import py
# import pytest
from cfn_tools import load_yaml

from aws_deploy.cloudformation.template import CloudformationTemplate
from aws_deploy.config import Config, ServiceConfig, ServiceType

# Sample service configuration
sample_service = ServiceConfig(
    Name="test-service",
    ShortName="ts",
    Type=ServiceType.CORE
)

# Sample YAML template content
sample_template_content = """
Resources:
  TestResource:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: test-bucket
Parameters:
  TestParam:
    Type: String
    Default: 'test'
"""

# Create a temporary directory for the test


def test_from_short_name(tmpdir: py.path.local, monkeypatch):
    tmp_core_dir = os.path.join(tmpdir, "core")
    os.makedirs(tmp_core_dir)
    with open(os.path.join(tmpdir, "core", "test-service.yml"), "w") as f:
        f.write(sample_template_content)

    # Mock the Config.find_service method to return the sample_service

    def mock_find_service(*attr):
        return sample_service

    monkeypatch.setattr(Config, "find_service", mock_find_service)

    # Test the CloudformationTemplate.from_short_name method
    cfn_template = CloudformationTemplate.from_short_name(
        "ts", tmp_core_dir)

    assert cfn_template.service.Name == "test-service"
    assert cfn_template.content == load_yaml(sample_template_content)
    assert "TestParam" in cfn_template.parameters
    assert cfn_template.service == sample_service
