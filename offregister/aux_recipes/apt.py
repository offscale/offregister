from itertools import imap, ifilterfalse
from functools import partial
from operator import is_
from fabric.api import run, sudo, cd
from offregister.utils import get_tempdir_fab


def is_installed(*packages):
    return tuple(ifilterfalse(partial(is_, True),
                              imap(lambda package: run('dpkg -s {package}'.format(package=package),
                                                       quiet=True, warn_only=True).succeeded or package,
                                   packages))
                 )


def apt_depend_factory(skip_apt_update=False):
    def apt_depend(*packages):
        more_to_install = is_installed(*packages)
        if not more_to_install:
            return None
        elif not skip_apt_update:
            sudo('apt-get update -qq')
        return sudo('apt-get install -y {packages}'.format(packages=' '.join(more_to_install)))

    return apt_depend


def download_and_install(url_prefix, packages):
    def one(package):
        run('curl -OL {url_prefix}{package}'.format(url_prefix=url_prefix, package=package))
        sudo('dpkg -i {package}'.format(package=package))

    with cd(get_tempdir_fab()):
        return map(one, packages)
