from fabric.api import run, sudo, cd, settings, local
from fabric.contrib.files import exists

from offregister.utils import get_tempdir_fab, which_true
from offregister.aux_recipes.go import ubuntu_install_go
from offregister.recipes.bosh import ubuntu_actually_install_bosh


def ubuntu_install_cloudfoundry(master):
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

    sudo('gem install bundler')
    loc_0 = 'deployments'
    run('mkdir {loc}'.format(loc=loc_0))
    with cd(loc_0):
        loc_1 = 'cf-example'
        run('mkdir {loc}'.format(loc=loc_0))
        with cd(loc_1):
            run('touch Gemfile')
            run('''source 'https://rubygems.org'
ruby "1.9.3"
gem "bosh_cli_plugin_aws"
            ''')
            run('bundle install')


def tpl():
    return '''export BOSH_VPC_DOMAIN=example.com
    export BOSH_VPC_SUBDOMAIN=my-subdomain
    export BOSH_AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID
    export BOSH_AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY
    export BOSH_AWS_REGION=us-east-1
    export BOSH_VPC_PRIMARY_AZ=us-east-1a
    export BOSH_VPC_SECONDARY_AZ=us-east-1b'''


def core_install_cloudfoundry():
    pass


def ubuntu_serve_cloudfoundry(domain, master):
    _serve_cloudfoundry(domain, master)


def core_serve_cloudfoundry():
    pass


def _serve_cloudfoundry(domain, master):
    run('bosh version')
    # run('bosh help')
    '''
    if master:
        run('bosh target {domain}'.format(domain=domain))
    '''
