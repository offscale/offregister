from os import path

from fabric.api import run, sudo, cd

from offregister.utils import get_tempdir_fab


def ubuntu_install_vulcand(*args, **kwargs):
    pass  # Unsupported at the moment, vulcand is CoreOS only. Porting would be another project :P


def core_install_vulcand(*args, **kwargs):
    run('git clone https://github.com/coreos/unit-examples.git')


def ubuntu_serve_vulcand(*args, **kwargs):
    return _serve_vulcand()


def core_serve_vulcand(*args, **kwargs):
    return _serve_vulcand()


def _serve_vulcand(domain):
    run('eval `ssh-agent -s`')
    run('vulcandctl install platform')
