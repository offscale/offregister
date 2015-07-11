from fabric.api import run, cd

from offregister.utils import get_tempdir_fab


def ubuntu_install_dokku():
    run('ssh-keygen -b 2048 -t dsa -f ~/.ssh/id_dsa -q -N ""')
    run('wget https://raw.github.com/progrium/dokku/v0.3.18/bootstrap.sh')
    run('sudo DOKKU_TAG=v0.3.18 bash bootstrap.sh')
    '''
    run('curl --silent https://get.docker.io/gpg 2> /dev/null | apt-key add - 2>&1 >/dev/null')
    run('curl --silent https://packagecloud.io/gpg.key 2> /dev/null | apt-key add - 2>&1 >/dev/null')

    run('echo "deb http://get.docker.io/ubuntu docker main" | sudo tee -a /etc/apt/sources.list.d/docker.list')
    run('echo "deb https://packagecloud.io/dokku/dokku/ubuntu/ trusty main" | sudo tee -a /etc/apt/sources.list.d/dokku.list')
    '''
    '''
    run('sudo apt-get update > /dev/null')
    run('sudo apt-get install -qq -y linux-image-extra-`uname -r` apt-transport-https')
    run('echo "dokku dokku/vhost_enable boolean true" | debconf-set-selections')
    run('sudo apt-get install -qq -y dokku')
    '''

def core_install_dokku():
    # run('wget https://raw.github.com/progrium/dokku/v0.3.18/bootstrap.sh')
    # run('sudo DOKKU_TAG=v0.3.18 bash bootstrap.sh')
    pass
