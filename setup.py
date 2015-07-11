from setuptools import setup, find_packages
from os import path
from functools import partial
from itertools import imap, ifilter
from ast import parse
from pip import __file__ as pip_loc

if __name__ == '__main__':
    package_name = 'offregister'

    f_for = lambda dir_name: partial(path.join, path.dirname(__file__), package_name, dir_name)
    d_for = lambda dir_name: path.join(path.dirname(path.dirname(pip_loc)), package_name, dir_name)

    _data_join = f_for('_data')
    _data_install_dir = d_for('_data')

    get_vals = lambda var0, var1: imap(lambda buf: next(imap(lambda e: e.value.s, parse(buf).body)),
                                       ifilter(lambda line: line.startswith(var0) or line.startswith(var1), f))

    with open(path.join(package_name, '__init__.py')) as f:
        __author__, __version__ = get_vals('__version__', '__author__')

    setup(
        name=package_name,
        author=__author__,
        version=__version__,
        test_suite=package_name + '.tests',
        packages=find_packages(),
        package_dir={package_name: package_name},
        install_requires=['apache-libcloud', 'python-etcd', 'fabric'],
        data_files=[
            (_data_install_dir, [_data_join('logging.yml')])
        ]
    )
