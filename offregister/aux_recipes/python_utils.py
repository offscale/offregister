from itertools import ifilterfalse, imap
from operator import is_
from functools import partial
from fabric.api import run


def mkvirtualenv_if_needed_factory(extra_args='-p /usr/bin/python3.4'):
    def mkvirtualenv_if_needed(*env_names):
        return tuple(ifilterfalse(partial(is_, False),
                                  imap(lambda env_name: run(
                                          "lsvirtualenv | grep -q '{env_name}'".format(env_name=env_name),
                                          warn_only=True, quiet=True).failed and run(
                                          "mkvirtualenv '{env_name}' {extra_args}".format(
                                                  env_name=env_name, extra_args=extra_args), warn_only=True) and env_name,
                                       env_names)))

    return mkvirtualenv_if_needed
