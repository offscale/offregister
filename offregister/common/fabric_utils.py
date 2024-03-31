# -*- coding: utf-8 -*-
from offregister.utils import App, sym2mod


def get_tempdir_fab(c, run_command=None, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    return (run_command or c.run)(
        "python -c 'from tempfile import gettempdir; print gettempdir()'", **kwargs
    ).stdout


def cmd_avail(c, command, run_command=None, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    installed = (run_command or c.run)(
        "command -v {command} >/dev/null".format(command=command),
        **kwargs,
        warn=False,
    )
    return installed.exited == 0


def append_path(c, new_path):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    installed = c.run(
        "grep -q {new_path} /etc/environment".format(new_path=new_path), warn=False
    )

    if installed.exited != 0:
        c.sudo(
            """sed -e '/^PATH/s/"$/:{new_path}"/g' -i /etc/environment""".format(
                new_path=new_path.replace("/", "\/")
            )
        )


def require(c, *apps, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    os_name = kwargs["os"]
    for app in apps:
        if not isinstance(app, App):
            raise TypeError("Expecting `App` got: {!r}".format(app))
        elif not app.name:
            raise ValueError("App must have name")

        if cmd_avail(c, app.name):
            c.local("echo {command} is already installed".format(command=app.name))
        else:
            try:
                sym2mod["_".join((os_name, "install", app.name))]()
            except KeyError as e:
                raise ImportError(e)

    def dec(f):
        def inner(*args, **kwargs):
            return f(*args, **kwargs)

        return inner

    return dec
