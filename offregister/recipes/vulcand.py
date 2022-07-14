from offregister_fab_utils.fs import cmd_avail
from offregister_fab_utils.git import clone_or_update


def ubuntu_install_vulcand(c, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    pass  # Unsupported at the moment, vulcand is CoreOS only. Porting would be another project :P


def core_install_vulcand(c, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    clone_or_update(c, team="coreos", repo="unit-examples")


def ubuntu_serve_vulcand(c, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    return _serve_vulcand(c, *args, **kwargs)


def core_serve_vulcand(c, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    return _serve_vulcand(c, *args, **kwargs)


def _serve_vulcand(c, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    command = "vulcandctl"
    if cmd_avail(c, command):
        raise EnvironmentError("Install {command} first".format(command=command))

    c.run("eval `ssh-agent -s`")
    c.run("vulcandctl install platform")
