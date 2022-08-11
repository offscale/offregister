from os import environ

from offregister_fab_utils.apt import apt_depends

from offregister.aux_recipes.dokku_plugin import install_plugin


def ubuntu_install_dokku(c, domain, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """

    apt_depends(c, "curl")
    c.run(
        "curl -sL https://get.docker.io/gpg 2> /dev/null | sudo apt-key add - 2>&1 >/dev/null"
    )
    c.run(
        "curl -sL https://packagecloud.io/gpg.key 2> /dev/null | sudo apt-key add - 2>&1 >/dev/null"
    )

    c.sudo(
        'echo "deb http://get.docker.io/ubuntu docker main" > /etc/apt/sources.list.d/docker.list'
    )
    c.sudo(
        'echo "deb https://packagecloud.io/dokku/dokku/ubuntu/ trusty main" > /etc/apt/sources.list.d/dokku.list'
    )

    uname_r = c.run("uname -r").stdout.rstrip()
    apt_depends(
        c, "linux-image-extra-{uname_r}".format(uname_r=uname_r), "apt-transport-https"
    )

    c.sudo('echo "dokku dokku/web_config boolean false" | debconf-set-selections')
    c.sudo('echo "dokku dokku/vhost_enable boolean true" | debconf-set-selections')
    c.sudo(
        'echo "dokku dokku/hostname string {domain}" | debconf-set-selections'.format(
            domain=domain
        )
    )

    # TODO: Something better than this:
    pub_key_path = "/root/.ssh/id_rsa.pub"
    c.put(environ["PUBLIC_KEY_PATH"], pub_key_path, use_sudo=True, mode=0o400)

    c.sudo(
        'echo "dokku dokku/key_file string {pub_key_path}" | debconf-set-selections'.format(
            pub_key_path=pub_key_path
        )
    )
    apt_depends(c, "dokku")

    """
    c.run('ssh-keygen -b 2048 -t dsa -f ~/.ssh/id_dsa -q -N ""')
    c.run('wget https://raw.github.com/progrium/dokku/v0.3.18/bootstrap.sh')
    c.run('sudo DOKKU_TAG=v0.3.18 bash bootstrap.sh')
    """
    """
    c.run('curl --silent https://get.docker.io/gpg 2> /dev/null | apt-key add - 2>&1 >/dev/null')
    c.run('curl --silent https://packagecloud.io/gpg.key 2> /dev/null | apt-key add - 2>&1 >/dev/null')

    c.run('echo "deb http://get.docker.io/ubuntu docker main" | sudo tee -a /etc/apt/sources.list.d/docker.list')
    c.run('echo "deb https://packagecloud.io/dokku/dokku/ubuntu/ trusty main" | sudo tee -a /etc/apt/sources.list.d/dokku.list')
    """
    """
    c.run('sudo apt-get update > /dev/null')
    c.run('sudo apt-get install -qq -y linux-image-extra-`uname -r` apt-transport-https')
    c.run('echo "dokku dokku/vhost_enable boolean true" | debconf-set-selections')
    c.run('sudo apt-get install -qq -y dokku')
    """


def core_install_dokku(c, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    # c.run('wget https://raw.github.com/progrium/dokku/v0.3.18/bootstrap.sh')
    # c.run('sudo DOKKU_TAG=v0.3.18 bash bootstrap.sh')
    raise NotImplementedError()


def ubuntu_serve_dokku(*args, **kwargs):
    raise NotImplementedError()


def core_serve_dokku(*args, **kwargs):
    raise NotImplementedError()


def install_jenkins(c):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    install_plugin(c, "alessio", "dokku-jenkins", "jenkins")
