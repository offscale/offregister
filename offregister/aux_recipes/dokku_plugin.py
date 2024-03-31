# -*- coding: utf-8 -*-
from offregister_fab_utils.apt import apt_depends
from offregister_fab_utils.fs import cmd_avail
from offregister_fab_utils.git import clone_or_update


def install_plugin(c, repo_team, repo_name, location=None):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """

    apt_depends(c, "git")
    cmd = "dokku"
    if not cmd_avail(c, cmd):
        raise EnvironmentError(
            "Install {cmd} before installing plugins".format(cmd=cmd)
        )
    with c.cd("/var/lib/dokku/plugins"):
        clone_or_update(c, team=repo_team, repo=repo_name, to_dir=location or repo_name)
    c.run("dokku plugins-install")
