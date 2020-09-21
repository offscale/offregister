from __future__ import print_function

from fabric.api import run, local

from offregister_fab_utils.fs import cmd_avail
from offregister_fab_utils.apt import apt_depends


def ubuntu_install_flynn(*args, **kwargs):
    apt_depends("curl")
    command = "flynn"
    if cmd_avail(command):
        local("echo {command} is already installed".format(command=command))
        return

    # run('L=/usr/local/bin/flynn && curl -sSL -A "`uname -sp`" https://dl.flynn.io/cli | zcat >$L && chmod +x $L')
    run("sudo bash < <(curl -fsSL https://dl.flynn.io/install-flynn)")


def core_install_flynn(*args, **kwargs):
    raise NotImplementedError("Flynn not [yet?] implemented on CoreOS")


def ubuntu_serve_flynn(*args, **kwargs):
    print("kwargs =", kwargs)
    run("sudo flynn-host init --init-discovery=3")
    run("pgrep flynn || sudo start flynn-host")
    """
    run('sudo CLUSTER_DOMAIN={dns_name} flynn-host bootstrap --min-hosts=3 /etc/flynn/bootstrap-manifest.json'.format(
        dns_name=dns_name
    ))
    """
