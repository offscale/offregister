from fabric.api import run
from offregister_fab_utils.fs import cmd_avail
from offregister_fab_utils.git import clone_or_update


def ubuntu_install_vulcand(*args, **kwargs):
    pass  # Unsupported at the moment, vulcand is CoreOS only. Porting would be another project :P


def core_install_vulcand(*args, **kwargs):
    clone_or_update(team="coreos", repo="unit-examples")


def ubuntu_serve_vulcand(*args, **kwargs):
    return _serve_vulcand(**kwargs)


def core_serve_vulcand(*args, **kwargs):
    return _serve_vulcand(**kwargs)


def _serve_vulcand(**kwargs):
    command = "vulcandctl"
    if cmd_avail(command):
        raise EnvironmentError("Install {command} first".format(command=command))

    run("eval `ssh-agent -s`")
    run("vulcandctl install platform")
