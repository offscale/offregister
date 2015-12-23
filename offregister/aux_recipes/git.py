from fabric.context_managers import cd
from fabric.contrib.files import exists
from fabric.operations import run


def clone_or_update(repo, branch='stable', remote='origin', team='offscale', to_dir=None):
    if exists(repo):
        with cd(repo):
            run('git fetch')
            run('git checkout -f {branch}'.format(branch=branch))
            run('git reset --hard {remote}/{branch}'.format(remote=remote, branch=branch))
        return 'updated'
    else:
        run('git clone https://github.com/{team}/{repo}.git {repo}'.format(team=team, repo=repo, to_dir=to_dir or repo))
        with cd(repo):
            run('git checkout -f {branch}'.format(branch=branch))
        return 'cloned'
