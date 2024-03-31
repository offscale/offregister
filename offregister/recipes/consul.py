# -*- coding: utf-8 -*-
def ubuntu_install_consul(c, *args, **kwargs):
    raise NotImplementedError()


def core_install_consul(c, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    c.run(
        "curl -L https://dl.bintray.com/mitchellh/consul/0.5.2_linux_amd64.zip | unzip -d "
    )
