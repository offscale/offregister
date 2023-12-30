# from offregister.aux_recipes.go import core_install_godep
from offregister_fab_utils.go import install as install_go


def ubuntu_install_deis(c, *args, **kwargs):
    raise NotImplementedError("Deis not implemented on Ubuntu")
    # Unsupported at the moment, deis is CoreOS only. Porting would be another project :P


def core_install_deis(c, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """

    install_go(c)  # core_install_godep
    """
    if c.run('which deisctl', warn=True).exited == 0:
        return  # TODO: Add prompt from fabric.contrib to see if they want to overwrite
    c.run('curl -sSL http://deis.io/deisctl/install.sh | sudo sh -s 1.8.0')
    # c.run('sudo ln -fs $PWD/deisctl /usr/local/bin/deisctl')
    c.run('deisctl --version')

    # Hacked together for now
    # c.run('ssh-keygen -q -t rsa -f ~/.ssh/deis -N '' -C deis')
    c.run('eval `ssh-agent -s`')
    c.run('ssh-add ~/.ssh/deis')
    c.run('deisctl config platform set sshPrivateKey=~/.ssh/deis')
    # c.run('make discovery-url')
    """


def ubuntu_serve_deis(domain):
    raise NotImplementedError("Deis not implemented on Ubuntu")


def core_serve_deis(c, private_ipv4, public_ipv4, domain, node_name, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """

    """
    c.run('eval `ssh-agent -s`')
    append('/etc/environment', 'DEISCTL_TUNNEL={DEISCTL_TUNNEL}'.format(DEISCTL_TUNNEL=domain), use_sudo=True)
    c.run('deisctl config platform set domain={domain}'.format(domain=domain))
    c.run('deisctl install platform')
    """
