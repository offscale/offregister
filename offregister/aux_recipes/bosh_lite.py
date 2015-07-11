from fabric.api import sudo, run, local

from offregister.utils import which_true


def install_bosh_lite():
    command = 'git'
    if which_true(command):
        local('echo {command} is already installed'.format(command=command))
    else:
        sudo('apt-get update -qq')
        sudo('apt-get install git')
