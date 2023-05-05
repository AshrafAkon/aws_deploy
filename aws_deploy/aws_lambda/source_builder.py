import os
import shutil
import tempfile

import docker

from aws_deploy.cloudformation.template import CloudformationTemplate
from aws_deploy.config import Config, console


class SourceBuilder:
    def __init__(self, template: CloudformationTemplate,
                 config: Config | None = None) -> None:
        self.template = template
        self.config = config if config else Config()

    def zip_file(self, zip_f_path):
        with open(f"{zip_f_path}.zip", 'rb') as file_data:
            bytes_content = file_data.read()
        return bytes_content

    def install_requirements(self, build_path: str):

        code_path = os.path.join(
            self.config.lambda_dir, self.template.service.Name)
        shutil.copytree(code_path, build_path, dirs_exist_ok=True)
        requirements_file_path = '/var/task/requirements.txt'

        client = docker.from_env()
        console.log('Installing lambda dependencies...')

        client.containers.run(
            image=f'public.ecr.aws/lambda/{self.config.lambda_python_version}',
            command="python -m pip install --target /var/task -r {}".format(
                requirements_file_path),
            entrypoint="",
            volumes={build_path: {'bind': '/var/task', 'mode': 'rw'}},

        )
        console.log("[green]Installed lambda dependencies.[/green]")

    def copy_source_to_build(self, base_dir: str, build_dir: str):
        shutil.copytree(base_dir, build_dir,
                        ignore=shutil.ignore_patterns(
                            'tests', 'requirements.txt'),
                        dirs_exist_ok=True)

    def make_archive(self, zip_f_path: str, build_dir: str):
        shutil.make_archive(zip_f_path, 'zip', build_dir)

    def build(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = os.path.join(self.config.lambda_dir,
                                    self.template.service.Name)
            build_dir = os.path.join(temp_dir, 'build')
            zip_f_path = os.path.join(temp_dir, 'build',
                                      self.template.service.Name)

            self.install_requirements(build_dir)
            self.copy_source_to_build(base_dir, build_dir)
            self.make_archive(zip_f_path, build_dir)

            zip_content = self.zip_file(zip_f_path)

        return zip_content
