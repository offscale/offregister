from os import path

from fabric.api import run, sudo, cd
from fabric.contrib.files import append

from offregister.common.fabric_utils import get_tempdir_fab
from offregister.aux_recipes.go import core_install_godep


def ubuntu_install_deis(*args, **kwargs):
    raise NotImplementedError("Deis not implemented on Ubuntu")
    # Unsupported at the moment, deis is CoreOS only. Porting would be another project :P


def core_install_deis(*args, **kwargs):
    core_install_godep()
    '''
    if run('which deisctl', warn_only=True).succeeded:
        return  # TODO: Add prompt from fabric.contrib to see if they want to overwrite
    run('curl -sSL http://deis.io/deisctl/install.sh | sudo sh -s 1.8.0')
    # run('sudo ln -fs $PWD/deisctl /usr/local/bin/deisctl')
    run('deisctl --version')

    # Hacked together for now
    # run('ssh-keygen -q -t rsa -f ~/.ssh/deis -N '' -C deis')
    run('eval `ssh-agent -s`')
    run('ssh-add ~/.ssh/deis')
    run('deisctl config platform set sshPrivateKey=~/.ssh/deis')
    # run('make discovery-url')
    '''


def ubuntu_serve_deis(domain):
    raise NotImplementedError("Deis not implemented on Ubuntu")


def core_serve_deis(private_ipv4, public_ipv4, domain, node_name, *args, **kwargs):
    '''
    run('eval `ssh-agent -s`')
    append('/etc/environment', 'DEISCTL_TUNNEL={DEISCTL_TUNNEL}'.format(DEISCTL_TUNNEL=domain), use_sudo=True)
    run('deisctl config platform set domain={domain}'.format(domain=domain))
    run('deisctl install platform')
    '''
