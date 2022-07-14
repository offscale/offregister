from os import path

from offregister_etcd.coreos import serve as coreos_serve_etcd
from offregister_etcd.ubuntu import install as install_etcd
from offregister_etcd.ubuntu import serve as serve_etcd
from offregister_fab_utils.fs import cmd_avail
from offregister_fab_utils.misc import upload_template_fmt
from pkg_resources import resource_filename


def ubuntu_install_coreos(c, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    # raise NotImplementedError("CoreOS on Ubuntu? - That'll be the day!")

    command = "etcd"
    if cmd_avail(c, command):
        c.local("echo {command} is already installed".format(command=command))
    else:
        install_etcd(c)

    status = c.run("status etcd2", warn=True, hide=True)
    if status.exited == 0:
        if not status.endswith("etcd2 stop/waiting"):
            c.sudo("stop etcd2")
    return "[ubuntu_install_coreos] etcd2 service stopped (so the conf can be updated)"


def core_install_coreos(c, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    # raise NotImplementedError('CoreOS on CoreOS? - Now that makes sense.')

    if c.run("systemctl status etcd2.service", warn=True, hide=True).exited == 0:
        c.sudo("systemctl stop etcd2.service")
    return "[core_install_coreos] etcd2 service stopped (so the conf can be updated)"


def ubuntu_serve_coreos(
    c,
    domain,
    node_name,
    public_ipv4,
    private_ipv4,
    etcd_discovery=None,
    size=3,
    *args,
    **kwargs
):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    serve_etcd(
        c,
        domain,
        node_name,
        public_ipv4,
        private_ipv4,
        etcd_discovery=etcd_discovery,
        size=size,
    )
    return "[ubuntu_serve_coreos] etcd2 service started"


def core_serve_coreos(
    c,
    domain,
    node_name,
    public_ipv4,
    private_ipv4,
    etcd_discovery=None,
    size=3,
    *args,
    **kwargs
):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    coreos_serve_etcd(
        domain, node_name, public_ipv4, private_ipv4, etcd_discovery=None, size=size
    )
    # conf file load
    c.sudo("mkdir -p /etc/systemd/system/fleet.socket.d")
    c.sudo("touch /etc/systemd/system/fleet.socket.d/30-ListenStream.conf")
    c.sudo("touch /var/run/fleet.sock")
    c.sudo("mkdir -p /etc/fleet/")
    c.sudo("touch /etc/fleet/fleet.conf")
    c.sudo(
        """echo 'public_ip="{public_ipv4}"' > /etc/fleet/fleet.conf""".format(
            public_ipv4=public_ipv4
        )
    )

    upload_template_fmt(
        c,
        path.join(
            path.dirname(resource_filename("offregister.aux_recipes", "__init__.py")),
            "templates",
            "fleet.systemd.conf",
        ),
        "/etc/systemd/system/fleet.socket.d/30-ListenStream.conf",
        context=locals(),
        use_sudo=True,
    )
    c.sudo("systemctl daemon-reload")
    c.sudo("systemctl start fleet.service")
    c.sudo("systemctl stop fleet.service")
    c.sudo("systemctl restart fleet.socket")
    c.sudo("systemctl start fleet.service")
    # fleetctl list-machines

    return "[core_serve_coreos] etcd2 service started"
