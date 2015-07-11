from fabric.api import sudo


def ubuntu_install_curl():
    sudo('apt-get install -y curl')
