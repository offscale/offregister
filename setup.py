from ast import parse
from distutils.sysconfig import get_python_lib
from functools import partial
from itertools import imap, ifilter
from os import path, listdir

from setuptools import setup, find_packages

if __name__ == '__main__':
    package_name = 'offregister'

    with open(path.join(package_name, '__init__.py')) as f:
        __author__, __version__ = imap(
            lambda buf: next(imap(lambda e: e.value.s, parse(buf).body)),
            ifilter(lambda line: line.startswith('__version__') or line.startswith('__author__'), f)
        )

    to_funcs = lambda *paths: (partial(path.join, path.dirname(__file__), package_name, *paths),
                               partial(path.join, get_python_lib(prefix=''), package_name, *paths))

    _data_join, _data_install_dir = to_funcs('_data')
    _config_join, _config_install_dir = to_funcs('_config')
    templates_join, templates_install_dir = to_funcs('aux_recipes', 'templates')

    setup(
        name=package_name,
        author=__author__,
        version=__version__,
        description='Configuration driven deployments with Fabric',
        classifiers=[
            'Development Status :: 7 - Inactive',
            'Intended Audience :: Developers',
            'Topic :: Software Development',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'License :: OSI Approved :: MIT License',
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 2 :: Only'
        ],
        test_suite=package_name + '.tests',
        packages=find_packages(),
        package_dir={package_name: package_name},
        install_requires=['pyyaml', 'apache-libcloud', 'python-etcd', 'fabric==1.14.0'],
        data_files=[
            (_data_install_dir(), map(_data_join, listdir(_data_join()))),
            (_config_install_dir(), map(_config_join, listdir(_config_join()))),
            (templates_install_dir(), map(templates_join, listdir(templates_join())))
        ]
    )
