from fabric.api import run, cd

from offregister.utils import get_tempdir_fab


def ubuntu_install_tsuru(*args, **kwargs):
    run('curl -sL https://raw.githubusercontent.com/tsuru/now/master/run.bash | bash')


def core_install_tsuru(*args, **kwargs):
    return


def ubuntu_serve_tsuru(*args, **kwargs):
    pass


def core_serve_tsuru(*args, **kwargs):
    pass
