from fabric.api import run, sudo
from fabric.contrib.files import append

from offregister.utils import append_path


def ubuntu_install_go(version='1.5.1', arch='amd64', GOROOT=None):
    if not GOROOT:
        HOME = run('echo $HOME')
        GOROOT = '{HOME}/go'.format(HOME=HOME)

    os = 'linux'
    install_loc = '/usr/local'
    go_tar = 'go{version}.{os}-{arch}.tar.gz'.format(version=version, os=os, arch=arch)

    run('curl -O https://storage.googleapis.com/golang/{go_tar}'.format(go_tar=go_tar))
    sudo('tar -C {install_loc} -xzf {go_tar}'.format(install_loc=install_loc, go_tar=go_tar))
    append_path('{install_loc}/go/bin'.format(install_loc=install_loc))
    append('/etc/environment', 'GOROOT={GOROOT}'.format(GOROOT=GOROOT), use_sudo=True)
    run('rm {go_tar}'.format(go_tar=go_tar))
    # run('rm -rf go*')
    run('mkdir {GOROOT}'.format(GOROOT=GOROOT))


def core_install_godep():
    run('go get github.com/tools/godep')
