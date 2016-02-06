from os import path
from pkg_resources import resource_filename

from fabric.api import run, sudo, local
from fabric.contrib.files import append, upload_template

from offregister_fab_utils.fs import cmd_avail
from offregister_etcd.ubuntu import install as install_etcd, serve as serve_etcd
from offregister_etcd.coreos import serve as coreos_serve_etcd


def ubuntu_install_coreos(*args, **kwargs):
    # raise NotImplementedError("CoreOS on Ubuntu? - That'll be the day!")

    command = 'etcd'
    if cmd_avail(command):
        local('echo {command} is already installed'.format(command=command))
    else:
        install_etcd()

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
    serve_etcd(domain, node_name, public_ipv4, private_ipv4, etcd_discovery=etcd_discovery, size=size)
    return '[ubuntu_serve_coreos] etcd2 service started'


def core_serve_coreos(domain, node_name, public_ipv4, private_ipv4, etcd_discovery=None, size=3, *args, **kwargs):
    coreos_serve_etcd(domain, node_name, public_ipv4, private_ipv4, etcd_discovery=None, size=size)
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
