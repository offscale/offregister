from offregister_fab_utils.fs import cmd_avail
from offregister_fab_utils.go import install as install_go

from offregister.recipes.bosh import ubuntu_actually_install_bosh


def ubuntu_install_cloudfoundry(c, master, *args, **kwargs):
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

    c.sudo("gem install bundler")
    loc_0 = "deployments"
    c.run("mkdir {loc}".format(loc=loc_0))
    with c.cd(loc_0):
        loc_1 = "cf-example"
        c.run("mkdir {loc}".format(loc=loc_0))
        with c.cd(loc_1):
            c.run("touch Gemfile")
            c.run(
                """source 'https://rubygems.org'
ruby "1.9.3"
gem "bosh_cli_plugin_aws"
            """
            )
            c.run("bundle install")


def tpl():
    return """export BOSH_VPC_DOMAIN=example.com
    export BOSH_VPC_SUBDOMAIN=my-subdomain
    export BOSH_AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID
    export BOSH_AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY
    export BOSH_AWS_REGION=us-east-1
    export BOSH_VPC_PRIMARY_AZ=us-east-1a
    export BOSH_VPC_SECONDARY_AZ=us-east-1b"""


def core_install_cloudfoundry(*args, **kwargs):
    raise NotImplementedError()


def ubuntu_serve_cloudfoundry(c, domain, master, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    _serve_cloudfoundry(c, domain, master)


def core_serve_cloudfoundry(*args, **kwargs):
    raise NotImplementedError()


def _serve_cloudfoundry(c, domain, master):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    c.run("bosh version")
    # c.run('bosh help')
    """
    if master:
        c.run('bosh target {domain}'.format(domain=domain))
    """
