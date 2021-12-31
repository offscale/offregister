from fabric.api import run
from offregister_fab_utils.apt import apt_depends


def ubuntu_install_tsuru(*args, **kwargs):
    apt_depends("curl")
    run("curl -sL https://raw.githubusercontent.com/tsuru/now/master/run.bash | bash")


def core_install_tsuru(*args, **kwargs):
    return


def ubuntu_serve_tsuru(*args, **kwargs):
    pass


def core_serve_tsuru(*args, **kwargs):
    pass
