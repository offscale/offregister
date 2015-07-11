from os import path

from fabric.api import run, sudo, cd

from offregister.utils import get_tempdir_fab


def ubuntu_install_deis():
    raise NotImplementedError("Deis not implemented on Ubuntu")
    pass  # Unsupported at the moment, deis is CoreOS only. Porting would be another project :P


def core_install_deis():
    if run('which deisctl', warn_only=True).succeeded:
        return  # TODO: Add prompt from fabric.contrib to see if they want to overwrite
    run('curl -sSL http://deis.io/deisctl/install.sh | sh -s 1.6.1')
    # run('sudo ln -fs $PWD/deisctl /usr/local/bin/deisctl')
    run('deisctl --version')

    # Hacked together for now
    run('ssh-keygen -q -t rsa -f ~/.ssh/deis -N '' -C deis')
    run('make discovery-url')


def ubuntu_serve_deis(domain):
    raise NotImplementedError("Deis not implemented on Ubuntu")
    return _serve_deis('')


def core_serve_deis():
    return _serve_deis('')


def _serve_deis(domain):
    run('eval `ssh-agent -s`')
    run('deisctl config platform set domain={domain}'.format(domain=domain))
    run('deisctl install platform')
