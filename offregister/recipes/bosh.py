# -*- coding: utf-8 -*-
from offregister_fab_utils.apt import apt_depends
from offregister_fab_utils.fs import cmd_avail
from offregister_fab_utils.go import install as install_go


def ubuntu_install_bosh(c, master, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    # DEPS, TODO: @depends(['go', 'bosh', 'vagrant'])
    command = "go"
    if cmd_avail(c, command):
        c.local("echo {command} is already installed".format(command=command))
    else:
        install_go(c)

    command = "bosh"
    if cmd_avail(c, command):
        c.local("echo {command} is already installed".format(command=command))
    else:
        ubuntu_actually_install_bosh(c, master)


def ubuntu_actually_install_bosh(c, master, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    apt_depends(
        c,
        "curl",
        "build-essential",
        "ruby",
        "ruby-dev",
        "libxml2-dev",
        "libsqlite3-dev",
        "libxslt1-dev",
        "libpq-dev",
        "libmysqlclient-dev",
    )
    c.sudo("gem install bosh_cli bosh_cli_plugin_micro --no-ri --no-rdoc")
    """sudo(
        'curl -s https://raw.githubusercontent.com/cloudfoundry-community/traveling-bosh/master/scripts/installer '
        '| bash'
    )"""


def core_install_bosh(c, *args, **kwargs):
    raise NotImplementedError()


def ubuntu_serve_bosh(c, domain, master, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    _serve_bosh(c, domain, master)


def core_serve_bosh(c, *args, **kwargs):
    raise NotImplementedError()


def _serve_bosh(c, domain, master):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    command = "bosh"
    if not cmd_avail(c, command):
        ubuntu_install_bosh(c, master)
    c.run("bosh version")
    # c.run('bosh help')
    """
    if master:
        c.run('bosh target {domain}'.format(domain=domain))
    """
