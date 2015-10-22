from os import path
from pkg_resources import resource_filename

from etcd import EtcdKeyNotFound

from fabric.api import run, sudo, cd, local, settings
from fabric.contrib.files import append, upload_template

from offutils import it_consumes
from offregister.utils import get_tempdir_fab, which_true  # , App, require
from offregister.aux_recipes.go import ubuntu_install_go
from offregister.aux_recipes.base import ubuntu_install_curl, ubuntu_install_apt_update

from offutils_strategy_register import _get_client as get_client


# @require(App('apt_update'), App('curl'), App('go'), os='ubuntu')
def ubuntu_install_etcd(version='v2.2.0', *args, **kwargs):
    it_consumes(
        local('echo {command} is already installed'.format(command=command)) if which_true(command)
        else globals()['_'.join(('ubuntu', 'install', command))]()
        for command in ('apt_update', 'curl', 'go')
    )

    command = 'etcd'
    if which_true(command):
        local('echo {command} is already installed'.format(command=command))
        return

    tempdir = get_tempdir_fab(run_command=run)

    install_dir = path.join(tempdir, version, run('date +%s'))
    run('mkdir -p {install_dir}'.format(install_dir=install_dir))

    with cd(install_dir):
        run(
            'curl -O -L '
            'https://github.com/coreos/etcd/releases/download/{version}/etcd-{version}-linux-amd64.tar.gz'.format(
                version=version
            )
        )
        run('tar xf etcd-{version}-linux-amd64.tar.gz'.format(version=version))
        run('sudo mv etcd-{version}-linux-amd64/etcd /usr/local/bin'.format(version=version))
        run('sudo mv etcd-{version}-linux-amd64/etcdctl /usr/local/bin'.format(version=version))
    run('logout')  # Need to get stuff from /etc/environment on next run


def ubuntu_serve_etcd(domain, node_name, public_ipv4, private_ipv4, etcd_discovery=None, size=3, *args, **kwargs):
    command = 'etcd --version'
    if run(command, quiet=True, warn_only=True).failed:
        raise EnvironmentError('Expected etcd to be installed')

    with settings(warn_only=True, quiet=True):
        service_install = sudo('initctl list | grep etcd2')
    if service_install.succeeded:
        if sudo('status etcd2').endswith('stop/waiting'):
            sudo('start etcd2')
        if etcd_discovery:
            return etcd_discovery
        return run('env | grep ETCD_DISCOVERY= | colrm 1 15')

    client = get_client()
    etcd_discovery = get_etcd_discovery_url(client, etcd_discovery, size)
    append('/etc/environment', 'ETCD_DISCOVERY={etcd_discovery}'.format(etcd_discovery=etcd_discovery),
           use_sudo=True)
    data_dir = '/var/etcd2_data_dir'
    sudo('mkdir {data_dir}'.format(data_dir=data_dir))
    upload_template(
        path.join(path.dirname(resource_filename('offregister.aux_recipes', '__init__.py')), 'templates',
                  'etcd2.upstart.conf'),
        '/etc/init/etcd2.conf', context=locals(), use_sudo=True
    )
    sudo('initctl reload-configuration')
    sudo('start etcd2')
    return etcd_discovery


def ubuntu_tail_etcd(method_args):
    sudo('initctl list | grep etcd')  # Chuck error if it's not installed
    sudo('tail {method_args} /var/log/upstart/etcd2.log'.format(method_args=method_args))


def core_install_etcd(*args, **kwargs):
    pass  # etcd is installed by default


def core_serve_etcd(domain, node_name, public_ipv4, private_ipv4, etcd_discovery=None, size=3, *args, **kwargs):
    # etcd is from coreos, so doesn't need to be [manually] installed!
    client = get_client()
    etcd_discovery = get_etcd_discovery_url(client, etcd_discovery, size)

    upload_template(
        path.join(path.dirname(resource_filename('offregister.aux_recipes', '__init__.py')),
                  'templates', 'etcd2.systemd.conf'),
        '/run/systemd/system/etcd2.service.d/10-oem.conf', context=locals(), use_sudo=True
    )

    if run('systemctl status etcd2.service', warn_only=True, quiet=True).failed:
        sudo('systemctl start etcd2.service')

    run('systemctl status etcd2.service')
    sudo('systemctl daemon-reload')


def get_etcd_discovery_url(client, etcd_discovery, size):
    try:
        etcd_discovery = client.get('/coreos/discovery').value
    except EtcdKeyNotFound:
        etcd_discovery = etcd_discovery or run('curl https://discovery.etcd.io/new?size={size}'.format(size=size))
        client.set('/coreos/discovery', etcd_discovery)

    return etcd_discovery
