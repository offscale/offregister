import importlib
import pkgutil

from pip import get_installed_distributions
from pip.commands import install
from sys import stderr
from collections import namedtuple
from types import FunctionType

from etcd import Client
from fabric.api import run, settings, local, sudo


def cluster_key(node_name, *clusters, **client_kwargs):
    key_name = '/unclustered/{node_name}'.format(node_name=node_name)

    client = Client(**client_kwargs)
    client.get_lock(key_name, ttl=60)
    value = client.get(key_name).value

    for cluster in clusters:
        client.set('/{cluster}/{node_name}'.format(cluster=cluster, node_name=node_name), value)

    return client.delete(key_name)


def get_tempdir_fab(run_command=run, **kwargs):
    return run("python -c 'from tempfile import gettempdir; print gettempdir()'", **kwargs)


def cmd_avail(command, run_command=run, **kwargs):
    with settings(warn_only=True):
        installed = run_command('command -v {command} >/dev/null'.format(command=command), **kwargs)
    return installed.succeeded


def append_path(new_path):
    with settings(warn_only=True):
        installed = run('grep -q {new_path} /etc/environment'.format(new_path=new_path))

    if installed.failed:
        sudo('''sed -e '/^PATH/s/"$/:{new_path}"/g' -i /etc/environment'''.format(
            new_path=new_path.replace('/', '\/')
        ))


def import_submodules(package, recursive=True):
    """ Import all submodules of a module, recursively, including subpackages

    :param package: package (name or actual module)
    :type package: str | module
    :rtype: dict[str, types.ModuleType]
    """
    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name
        try:
            results[full_name] = importlib.import_module(full_name)
            if recursive and is_pkg:
                results.update(import_submodules(full_name))
        except ImportError:
            print >> stderr, '[sym2mod] Failed to import: {!r}'.format(full_name)
    return results


def create_symbol_module_d(module_name_module_d, include=None, exclude=None, condition=None):
    """ Create mapping of symbol to module

    :param module_name_module_d
    :type module_name_module_d: dict[str, types.ModuleType]
    :rtype: dict[str, types.FunctionType|types.ClassType|types.TupleType]
    """
    inv_res = {}
    for mod in module_name_module_d.itervalues():
        for sym in dir(mod):
            if type(condition) is not FunctionType or condition(sym):
                if include and sym in include:
                    inv_res[sym] = mod
                elif exclude and sym not in exclude:
                    inv_res[sym] = mod
                else:
                    inv_res[sym] = mod
    return inv_res


sym2mod = create_symbol_module_d(import_submodules('offregister'), condition=lambda s: not s.startswith('_'))

App = namedtuple('App', ('name', 'version'))
App.__new__.__defaults__ = None, None


def require(*apps, **kwargs):
    os_name = kwargs['os']
    for app in apps:
        if not isinstance(app, App):
            raise TypeError('Expecting `App` got: {!r}'.format(app))
        elif not app.name:
            raise ValueError('App must have name')
        command = 'curl'

        if cmd_avail(app.name):
            local('echo {command} is already installed'.format(command=app.name))
        else:
            try:
                sym2mod['_'.join((os_name, 'install', app.name))]()
            except KeyError as e:
                raise ImportError(e)

    def dec(f):
        def inner(*args, **kwargs):
            return f(*args, **kwargs)

        return inner

    return dec


def get_pip_packages():
    return map(lambda s: s.project_name, get_installed_distributions())


def pip_install(package, options_attr=None):
    install_cmd = install.InstallCommand()
    options, args = install_cmd.parse_args([package])
    if options_attr:
        for opt_name, opt_val in options_attr.iteritems():
            setattr(options, opt_name, opt_val)
    return install_cmd.run(options, args)
