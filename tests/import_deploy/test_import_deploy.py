from aws_deploy.cloudformation.parameter import ssm_stored
from aws_deploy.main import import_deploy


def test_import_deploy():
    # assets_dir = os.path.join(os.path.dirname(
    #     os.path.abspath(__file__)), 'assets')
    # os.chdir(assets_dir)

    import_deploy()
    from aws_deploy.cloudformation.parameter.resolver import ResolverFactory

    resolver = ResolverFactory()

    assert resolver.get('testTokeStore') is ssm_stored.UpdatableSSM
