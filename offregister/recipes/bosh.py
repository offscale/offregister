from fabric.api import local, run, sudo
from offregister_fab_utils.apt import apt_depends
from offregister_fab_utils.fs import cmd_avail
from offregister_fab_utils.go import install as install_go


def ubuntu_install_bosh(master, *args, **kwargs):
    # DEPS, TODO: @depends(['go', 'bosh', 'vagrant'])
    command = "go"
    if cmd_avail(command):
        local("echo {command} is already installed".format(command=command))
    else:
        install_go()

    command = "bosh"
    if cmd_avail(command):
        local("echo {command} is already installed".format(command=command))
    else:
        ubuntu_actually_install_bosh(master)


def ubuntu_actually_install_bosh(master, *args, **kwargs):
    apt_depends(
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
    sudo("gem install bosh_cli bosh_cli_plugin_micro --no-ri --no-rdoc")
    """sudo(
        'curl -s https://raw.githubusercontent.com/cloudfoundry-community/traveling-bosh/master/scripts/installer '
        '| bash'
    )"""


def core_install_bosh(*args, **kwargs):
    raise NotImplementedError()


def ubuntu_serve_bosh(domain, master, *args, **kwargs):
    _serve_bosh(domain, master)


def core_serve_bosh(*args, **kwargs):
    raise NotImplementedError()


def _serve_bosh(domain, master):
    command = "bosh"
    if not cmd_avail(command):
        ubuntu_install_bosh(master)
    run("bosh version")
    # run('bosh help')
    """
    if master:
        run('bosh target {domain}'.format(domain=domain))
    """
