from offregister_fab_utils.apt import apt_depends


def install_bosh_lite():
    apt_depends("git")
