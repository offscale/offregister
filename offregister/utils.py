import importlib
import pkgutil
from collections import namedtuple
from sys import stderr
from types import FunctionType

from etcd import Client
from pip import get_installed_distributions
from pip.commands import install


def cluster_key(node_name, *clusters, **client_kwargs):
    key_name = '/unclustered/{node_name}'.format(node_name=node_name)

    client = Client(**client_kwargs)
    client.get_lock(key_name, ttl=60)
    value = client.get(key_name).value

    for cluster in clusters:
        client.set('/{cluster}/{node_name}'.format(cluster=cluster, node_name=node_name), value)

    return client.delete(key_name)


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


def get_pip_packages():
    return map(lambda s: s.project_name, get_installed_distributions())


def pip_install(package, options_attr=None):
    install_cmd = install.InstallCommand()
    options, args = install_cmd.parse_args([package])
    if options_attr:
        for opt_name, opt_val in options_attr.iteritems():
            setattr(options, opt_name, opt_val)
    return install_cmd.run(options, args)


def guess_os_username(node, hint=None):
    driver_name = node.driver.__class__.__name__.lower()
    if hint and 'softlayer' in hint.lower() or driver_name in ('digitalocean', 'softlayernodedriver'):
        return 'root'
    elif driver_name == 'azure':
        return 'azureuser'
    elif driver_name == 'vagrant':
        return node.extra['user']

    node_name = node.name.lower()
    if 'ubuntu' in node_name:
        return 'ubuntu'
    elif 'core' in node_name:
        return 'core'
    return 'user'


def guess_os(node, hint=None):
    node_name = node.name.lower()
    if 'ubuntu' in node_name:
        return 'ubuntu'
    elif 'core' in node_name:
        return 'core'
    return hint or 'ubuntu'

# stolen from fabric.api!
Env = namedtuple('Env', ('disable_known_hosts', 'effective_roles', 'tasks', 'linewise', 'show', 'password',
                         'key_filename', 'abort_on_prompts', 'skip_unknown_tasks', 'reject_unknown_hosts',
                         'skip_bad_hosts', 'use_ssh_config', 'roledefs', 'gateway', 'gss_auth', 'keepalive',
                         'eagerly_disconnect', 'rcfile', 'path_behavior', 'hide', 'sudo_prefix', 'lcwd', 'no_agent',
                         'forward_agent', 'remote_interrupt', 'port', 'shell', 'version', 'use_exceptions_for',
                         'connection_attempts', 'hosts', 'gss_deleg', 'cwd', 'abort_exception', 'real_fabfile',
                         'passwords', 'sudo_password', 'host_string', 'shell_env', 'always_use_pty', 'colorize_errors',
                         'exclude_hosts', 'all_hosts', 'sudo_prompt', 'again_prompt', 'echo_stdin', 'user', 'gss_kex',
                         'command_timeout', 'path', 'local_user', 'combine_stderr', 'command_prefixes', 'dedupe_hosts',
                         'warn_only', 'no_keys', 'sudo_passwords', 'roles', 'fabfile', 'use_shell', 'host', 'pool_size',
                         'system_known_hosts', 'prompts', 'output_prefix', 'command', 'timeout', 'default_port',
                         'ssh_config_path', 'parallel', 'sudo_user', 'ok_ret_codes'))