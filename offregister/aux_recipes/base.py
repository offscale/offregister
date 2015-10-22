from fabric.api import sudo, local

from offregister.utils import get_tempdir_fab, which_true


def ubuntu_install_curl():
    command = 'curl'
    if which_true(command):
        local('echo {command} is already installed'.format(command=command))
    else:
        sudo('apt-get install -y curl')


def ubuntu_install_apt_update():  # YAY! - semantically incorrect namespacing
    sudo('apt-get update -qq')
