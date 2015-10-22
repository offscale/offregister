from os import path
from pkg_resources import resource_filename

from fabric.api import run, sudo, cd, local, settings
from fabric.contrib.files import append, upload_template

from offregister.utils import get_tempdir_fab, which_true
from offregister.recipes.etcd2 import (ubuntu_install_etcd, ubuntu_serve_etcd,
                                       core_serve_etcd,
                                       get_etcd_discovery_url)

from offutils_strategy_register import _get_client as get_client


def ubuntu_install_coreos(*args, **kwargs):
    # raise NotImplementedError("CoreOS on Ubuntu? - That'll be the day!")

    command = 'etcd'
    if which_true(command):
        local('echo {command} is already installed'.format(command=command))
    else:
        ubuntu_install_etcd()

    status = run('status etcd2', warn_only=True, quiet=True)
    if status.succeeded:
        if not status.endswith('etcd2 stop/waiting'):
            sudo('stop etcd2')
    return '[ubuntu_install_coreos] etcd2 service stopped (so the conf can be updated)'


def core_install_coreos(*args, **kwargs):
    # raise NotImplementedError('CoreOS on CoreOS? - Now that makes sense.')

    if run('systemctl status etcd2.service', warn_only=True, quiet=True).succeeded:
        sudo('systemctl stop etcd2.service')
    return '[core_install_coreos] etcd2 service stopped (so the conf can be updated)'


def ubuntu_serve_coreos(domain, node_name, public_ipv4, private_ipv4, etcd_discovery=None, size=3, *args, **kwargs):
    ubuntu_serve_etcd(domain, node_name, public_ipv4, private_ipv4, etcd_discovery=etcd_discovery, size=size)
    return '[ubuntu_serve_coreos] etcd2 service started'


def core_serve_coreos(domain, node_name, public_ipv4, private_ipv4, etcd_discovery=None, size=3, *args, **kwargs):
    core_serve_etcd(domain, node_name, public_ipv4, private_ipv4, etcd_discovery=None, size=size)
    # conf file load
    sudo('mkdir -p /etc/systemd/system/fleet.socket.d')
    sudo('touch /etc/systemd/system/fleet.socket.d/30-ListenStream.conf')
    sudo('touch /var/run/fleet.sock')
    sudo('mkdir -p /etc/fleet/')
    sudo('touch /etc/fleet/fleet.conf')
    sudo('''echo 'public_ip="{public_ipv4}"' > /etc/fleet/fleet.conf'''.format(public_ipv4=public_ipv4))

    upload_template(
        path.join(path.dirname(resource_filename('offregister.aux_recipes', '__init__.py')),
                  'templates', 'fleet.systemd.conf'),
        '/etc/systemd/system/fleet.socket.d/30-ListenStream.conf', context=locals(), use_sudo=True
    )
    sudo('systemctl daemon-reload')
    sudo('systemctl start fleet.service')
    sudo('systemctl stop fleet.service')
    sudo('systemctl restart fleet.socket')
    sudo('systemctl start fleet.service')
    # fleetctl list-machines

    return '[core_serve_coreos] etcd2 service started'
