import os

from aws_deploy.main import import_deploy


def test_import_deploy():
    assets_dir = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'assets')
    os.chdir(assets_dir)
    import_deploy()

    assert "test_function1" in globals(),\
        "test_function1 not found in namespace"
