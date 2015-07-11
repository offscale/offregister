from fabric.api import run, cd


def ubuntu_install_consul():
    return


def core_install_consul():
    run('curl -L https://dl.bintray.com/mitchellh/consul/0.5.2_linux_amd64.zip | unzip -d ')
    return
