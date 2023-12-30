# -*- coding: utf-8 -*-

from ast import parse
from functools import partial
from operator import attrgetter, itemgetter
from os import listdir, path
import sys

from setuptools import find_packages, setup

if sys.version_info[:2] >= (3, 12):
    import os
    from sysconfig import _BASE_EXEC_PREFIX as BASE_EXEC_PREFIX
    from sysconfig import _BASE_PREFIX as BASE_PREFIX
    from sysconfig import _EXEC_PREFIX as EXEC_PREFIX
    from sysconfig import _PREFIX as PREFIX
    from sysconfig import get_python_version

    def is_virtual_environment():
        """
        Whether one is in a virtual environment
        """
        return sys.base_prefix != sys.prefix or hasattr(sys, "real_prefix")

    def get_python_lib(plat_specific=0, standard_lib=0, prefix=None):
        """Return the directory containing the Python library (standard or
        site additions).

        If 'plat_specific' is true, return the directory containing
        platform-specific modules, i.e. any module from a non-pure-Python
        module distribution; otherwise, return the platform-shared library
        directory.  If 'standard_lib' is true, return the directory
        containing standard Python library modules; otherwise, return the
        directory for site-specific modules.

        If 'prefix' is supplied, use it instead of sys.base_prefix or
        sys.base_exec_prefix -- i.e., ignore 'plat_specific'.
        """
        is_default_prefix = not prefix or os.path.normpath(prefix) in (
            "/usr",
            "/usr/local",
        )
        if prefix is None:
            if standard_lib:
                prefix = plat_specific and BASE_EXEC_PREFIX or BASE_PREFIX
            else:
                prefix = plat_specific and EXEC_PREFIX or PREFIX

        if os.name == "posix":
            if plat_specific or standard_lib:
                # Platform-specific modules (any module from a non-pure-Python
                # module distribution) or standard Python library modules.
                libdir = sys.platlibdir
            else:
                # Pure Python
                libdir = "lib"
            libpython = os.path.join(prefix, libdir, "python" + get_python_version())
            if standard_lib:
                return libpython
            elif is_default_prefix and not is_virtual_environment():
                return os.path.join(prefix, "lib", "python3", "dist-packages")
            else:
                return os.path.join(libpython, "site-packages")
        elif os.name == "nt":
            if standard_lib:
                return os.path.join(prefix, "Lib")
            else:
                return os.path.join(prefix, "Lib", "site-packages")
        else:

            class DistutilsPlatformError(Exception):
                """DistutilsPlatformError"""

            raise DistutilsPlatformError(
                "I don't know where Python installs its library "
                "on platform '%s'" % os.name
            )

else:
    from distutils.sysconfig import get_python_lib

if sys.version_info[0] == 2:
    from itertools import ifilter as filter
    from itertools import imap as map


if __name__ == "__main__":
    package_name = "offregister"

    with open(path.join(package_name, "__init__.py")) as f:
        __author__, __version__ = map(
            lambda const: const.value if hasattr(const, "value") else const.s,
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
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
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
