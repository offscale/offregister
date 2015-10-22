from fabric.context_managers import cd
from fabric.operations import run


def install_plugin(repo_url, location=None):
    if not location:
        location = repo_url.rpartition('/')[2]
    with cd('/var/lib/dokku/plugins'):
        run('git clone {repo_url} {location}'.format(repo_url=repo_url, location=location))
    run('dokku plugins-install')
