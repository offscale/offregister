# -*- coding: utf-8 -*-

from ast import parse
from distutils.sysconfig import get_python_lib
from functools import partial
from operator import attrgetter, itemgetter
from os import listdir, path
from sys import version_info

from setuptools import find_packages, setup

if version_info[0] == 2:
    from itertools import ifilter as filter
    from itertools import imap as map


if __name__ == "__main__":
    package_name = "offregister"

    with open(path.join(package_name, "__init__.py")) as f:
        __author__, __version__ = map(
            lambda const: const.value if version_info > (3, 6) else const.s,
            map(
                attrgetter("value"),
                map(
                    itemgetter(0),
                    map(
                        attrgetter("body"),
                        map(
                            parse,
                            filter(
                                lambda line: line.startswith("__version__")
                                or line.startswith("__author__"),
                                f,
                            ),
                        ),
                    ),
                ),
            ),
        )

    to_funcs = lambda *paths: (
        partial(path.join, path.dirname(__file__), package_name, *paths),
        partial(path.join, get_python_lib(prefix=""), package_name, *paths),
    )

    _data_join, _data_install_dir = to_funcs("_data")
    _config_join, _config_install_dir = to_funcs("_config")
    templates_join, templates_install_dir = to_funcs("aux_recipes", "templates")

    setup(
        name=package_name,
        author=__author__,
        version=__version__,
        description="Configuration driven deployments with Fabric",
        classifiers=[
            "Development Status :: 7 - Inactive",
            "Intended Audience :: Developers",
            "Topic :: Software Development",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "License :: OSI Approved :: MIT License",
            "License :: OSI Approved :: Apache Software License",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2.7",
        ],
        test_suite=package_name + ".tests",
        packages=find_packages(),
        package_dir={package_name: package_name},
        install_requires=["pyyaml", "apache-libcloud", "etcd3"],
        data_files=[
            (_data_install_dir(), list(map(_data_join, listdir(_data_join())))),
            (_config_install_dir(), list(map(_config_join, listdir(_config_join())))),
            (
                templates_install_dir(),
                list(map(templates_join, listdir(templates_join()))),
            ),
        ],
    )
