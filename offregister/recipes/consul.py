from fabric.api import run


def ubuntu_install_consul(*args, **kwargs):
    raise NotImplementedError()


def core_install_consul(*args, **kwargs):
    run(
        "curl -L https://dl.bintray.com/mitchellh/consul/0.5.2_linux_amd64.zip | unzip -d "
    )
    return
