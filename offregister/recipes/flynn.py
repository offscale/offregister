from __future__ import print_function

from offregister_fab_utils.apt import apt_depends
from offregister_fab_utils.fs import cmd_avail


def ubuntu_install_flynn(c, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """

    apt_depends(c, "curl")
    command = "flynn"
    if cmd_avail(c, command):
        c.local("echo {command} is already installed".format(command=command))
        return

    # c.run('L=/usr/local/bin/flynn && curl -sSL -A "`uname -sp`" https://dl.flynn.io/cli | zcat >$L && chmod +x $L')
    c.run("sudo bash < <(curl -fsSL https://dl.flynn.io/install-flynn)")


def core_install_flynn(*args, **kwargs):
    raise NotImplementedError("Flynn not [yet?] implemented on CoreOS")


def ubuntu_serve_flynn(c, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    print("kwargs =", kwargs)
    c.run("sudo flynn-host init --init-discovery=3")
    c.run("pgrep flynn || sudo start flynn-host")
    """
    c.run('sudo CLUSTER_DOMAIN={dns_name} flynn-host bootstrap --min-hosts=3 /etc/flynn/bootstrap-manifest.json'.format(
        dns_name=dns_name
    ))
    """
