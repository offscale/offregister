from os import environ

from fabric.api import run, sudo
from fabric.contrib.files import put

from offregister.aux_recipes.dokku_plugin import install_plugin


def ubuntu_install_dokku(domain, *args, **kwargs):
    run('curl -sL https://get.docker.io/gpg 2> /dev/null | sudo apt-key add - 2>&1 >/dev/null')
    run('curl -sL https://packagecloud.io/gpg.key 2> /dev/null | sudo apt-key add - 2>&1 >/dev/null')

    sudo('echo "deb http://get.docker.io/ubuntu docker main" > /etc/apt/sources.list.d/docker.list')
    sudo('echo "deb https://packagecloud.io/dokku/dokku/ubuntu/ trusty main" > /etc/apt/sources.list.d/dokku.list')

    sudo('apt-get update -qq')
    sudo('apt-get install -qq -y linux-image-extra-`uname -r` apt-transport-https')

    sudo('echo "dokku dokku/web_config boolean false" | debconf-set-selections')
    sudo('echo "dokku dokku/vhost_enable boolean true" | debconf-set-selections')
    sudo('echo "dokku dokku/hostname string {domain}" | debconf-set-selections'.format(domain=domain))

    # TODO: Something better than this:
    pub_key_path = '/root/.ssh/id_rsa.pub'
    put(environ['PUBLIC_KEY_PATH'], pub_key_path, use_sudo=True, mode=0400)

    sudo('echo "dokku dokku/key_file string {pub_key_path}" | debconf-set-selections'.format(pub_key_path=pub_key_path))
    sudo('apt-get install -qq -y dokku')

    '''
    run('ssh-keygen -b 2048 -t dsa -f ~/.ssh/id_dsa -q -N ""')
    run('wget https://raw.github.com/progrium/dokku/v0.3.18/bootstrap.sh')
    run('sudo DOKKU_TAG=v0.3.18 bash bootstrap.sh')
    '''
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


def core_install_dokku(*args, **kwargs):
    # run('wget https://raw.github.com/progrium/dokku/v0.3.18/bootstrap.sh')
    # run('sudo DOKKU_TAG=v0.3.18 bash bootstrap.sh')
    raise NotImplementedError()


def ubuntu_serve_dokku(*args, **kwargs):
    pass


def core_serve_dokku(*args, **kwargs):
    raise NotImplementedError()


def install_jenkins():
    install_plugin('https://github.com/alessio/dokku-jenkins', 'jenkins')
