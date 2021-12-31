from fabric.api import local, run, settings, sudo

from offregister.utils import App, sym2mod


def get_tempdir_fab(run_command=run, **kwargs):
    return run(
        "python -c 'from tempfile import gettempdir; print gettempdir()'", **kwargs
    )


def cmd_avail(command, run_command=run, **kwargs):
    with settings(warn_only=True):
        installed = run_command(
            "command -v {command} >/dev/null".format(command=command), **kwargs
        )
    return installed.succeeded


def append_path(new_path):
    with settings(warn_only=True):
        installed = run("grep -q {new_path} /etc/environment".format(new_path=new_path))

    if installed.failed:
        sudo(
            """sed -e '/^PATH/s/"$/:{new_path}"/g' -i /etc/environment""".format(
                new_path=new_path.replace("/", "\/")
            )
        )


def require(*apps, **kwargs):
    os_name = kwargs["os"]
    for app in apps:
        if not isinstance(app, App):
            raise TypeError("Expecting `App` got: {!r}".format(app))
        elif not app.name:
            raise ValueError("App must have name")

        if cmd_avail(app.name):
            local("echo {command} is already installed".format(command=app.name))
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
