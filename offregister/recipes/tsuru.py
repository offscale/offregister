from offregister_fab_utils.apt import apt_depends


def ubuntu_install_tsuru(c, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    apt_depends(c, "curl")
    c.run("curl -sL https://raw.githubusercontent.com/tsuru/now/master/run.bash | bash")


def core_install_tsuru(c, *args, **kwargs):
    return


def ubuntu_serve_tsuru(c, *args, **kwargs):
    pass


def core_serve_tsuru(c, *args, **kwargs):
    pass
