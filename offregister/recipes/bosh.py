from fabric.api import run, sudo, cd, settings, local
from fabric.contrib.files import exists

from offregister.utils import get_tempdir_fab, which_true
from offregister.aux_recipes.go import ubuntu_install_go


def ubuntu_install_bosh(master, *args, **kwargs):
    # DEPS, TODO: @depends(['go', 'bosh', 'vagrant'])
    command = 'go'
    if which_true(command):
        local('echo {command} is already installed'.format(command=command))
    else:
        ubuntu_install_go()

    command = 'bosh'
    if which_true(command):
        local('echo {command} is already installed'.format(command=command))
    else:
        ubuntu_actually_install_bosh(master)


def ubuntu_actually_install_bosh(master, *args, **kwargs):
    sudo('apt-get update -qq')
    sudo('apt-get install -y build-essential ruby ruby-dev libxml2-dev libsqlite3-dev libxslt1-dev '
         'libpq-dev libmysqlclient-dev curl')
    sudo('gem install bosh_cli bosh_cli_plugin_micro --no-ri --no-rdoc')
    '''sudo(
        'curl -s https://raw.githubusercontent.com/cloudfoundry-community/traveling-bosh/master/scripts/installer '
        '| bash'
    )'''


def core_install_bosh(*args, **kwargs):
    raise NotImplementedError()


def ubuntu_serve_bosh(domain, master, *args, **kwargs):
    _serve_bosh(domain, master)


def core_serve_bosh(*args, **kwargs):
    raise NotImplementedError()


def _serve_bosh(domain, master):
    command = 'bosh'
    if not which_true(command):
        ubuntu_install_bosh(master)
    run('bosh version')
    # run('bosh help')
    '''
    if master:
        run('bosh target {domain}'.format(domain=domain))
    '''
