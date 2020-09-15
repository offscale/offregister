from fabric.context_managers import cd
from fabric.operations import run

from offregister_fab_utils.apt import apt_depends
from offregister_fab_utils.fs import cmd_avail
from offregister_fab_utils.git import clone_or_update


def install_plugin(repo_team, repo_name, location=None):
    apt_depends("git")
    cmd = "dokku"
    if not cmd_avail(cmd):
        raise EnvironmentError(
            "Install {cmd} before installing plugins".format(cmd=cmd)
        )
    with cd("/var/lib/dokku/plugins"):
        clone_or_update(team=repo_team, repo=repo_name, to_dir=location or repo_name)
    run("dokku plugins-install")
