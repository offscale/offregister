from os import path

from fabric.api import run, sudo, cd

from offregister.utils import get_tempdir_fab


def ubuntu_install_vulcand():
    pass  # Unsupported at the moment, vulcand is CoreOS only. Porting would be another project :P


def core_install_vulcand():
    run('git clone https://github.com/coreos/unit-examples.git')


def ubuntu_serve_vulcand():
    return _serve_vulcand()


def core_serve_vulcand():
    return _serve_vulcand()


def _serve_vulcand(domain):
    run('eval `ssh-agent -s`')
    run('vulcandctl install platform')
