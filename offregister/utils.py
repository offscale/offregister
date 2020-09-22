import importlib
import pkgutil
import runpy
import sys
from collections import namedtuple
from os import getcwd, chdir, path
from sys import modules
from types import FunctionType

import etcd3
from pip._internal.utils.misc import get_installed_distributions

from offregister import get_logger
from offutils.util import itervalues

logger = get_logger(modules[__name__].__name__)


def cluster_key(node_name, *clusters, **client_kwargs):
    key_name = "/unclustered/{node_name}".format(node_name=node_name)

    client = etcd3.client(**client_kwargs)
    with client.lock(key_name, ttl=60):
        value = client.get(key_name).value

        for cluster in clusters:
            client.set(
                "/{cluster}/{node_name}".format(cluster=cluster, node_name=node_name),
                value,
            )

        return client.delete(key_name)


def import_submodules(package, recursive=True):
    """Import all submodules of a module, recursively, including subpackages

    :param package: package (name or actual module)
    :type package: ```Union[str, module]```

    :param recursive: Whether to import subpackages also
    :type recursive: ```bool```

    :rtype: dict[str, types.ModuleType]
    """
    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + "." + name
        try:
            results[full_name] = importlib.import_module(full_name)
            if recursive and is_pkg:
                results.update(import_submodules(full_name))
        except ImportError:
            pass  # logger.warning('[sym2mod] Failed to import: {!r}'.format(full_name))
    return results


def create_symbol_module_d(
    module_name_module_d, include=None, exclude=None, condition=None
):
    """Create mapping of symbol to module

    :param module_name_module_d
    :type module_name_module_d: dict[str, types.ModuleType]
    :rtype: dict[str, types.FunctionType|types.ClassType|types.type(tuple)]
    """
    inv_res = {}
    for mod in itervalues(module_name_module_d):
        for sym in dir(mod):
            if type(condition) is not FunctionType or condition(sym):
                if include and sym in include:
                    inv_res[sym] = mod
                elif exclude and sym not in exclude:
                    inv_res[sym] = mod
                else:
                    inv_res[sym] = mod
    return inv_res


sym2mod = create_symbol_module_d(
    import_submodules("offregister"), condition=lambda s: not s.startswith("_")
)

App = namedtuple("App", ("name", "version"))
App.__new__.__defaults__ = None, None


def get_pip_packages():
    return [s.project_name for s in get_installed_distributions()]


def pip_install(package, options_attr=None):
    prev_wd = getcwd()
    prev_sys_argv = sys.argv

    pip_output = None
    try:
        sys.argv = ["pip", "install", "."]
        if options_attr is not None and "src_dir" in options_attr:
            src_dir = options_attr["src_dir"]
            if path.basename(src_dir) != package:
                src_dir = path.join(src_dir, package)
            chdir(src_dir)
        else:
            sys.argv[-1] = package

        pip_output = runpy.run_module("pip", run_name="__main__")

    except SystemExit as e:
        if e.code != 0:
            raise

        return pip_output

    finally:
        chdir(prev_wd)
        sys.argv = prev_sys_argv


def guess_os_username(node, hint=None):
    driver_name = node.driver.__class__.__name__.lower()
    if (
        hint
        and "softlayer" in hint.lower()
        or driver_name in ("digitalocean", "softlayernodedriver")
    ):
        return "root"
    elif driver_name == "azure":
        return "azureuser"
    elif driver_name == "vagrant":
        return node.extra["user"]

    node_name = node.name.lower()
    if "ubuntu" in node_name:
        return "ubuntu"
    elif "core" in node_name:
        return "core"
    return "user"


def guess_os(node, hint=None):
    node_name = node.name.lower()
    if node.extra and "os" in node.extra:
        return "{}".format(node.extra["os"])
    if "ubuntu" in node_name:
        return "ubuntu"
    elif "core" in node_name:
        return "core"
    return hint or "{}".format(node.extra["user"]) if "user" in node.extra else "ubuntu"


# stolen from fabric.api!
Env = namedtuple(
    "Env",
    (
        "disable_known_hosts",
        "effective_roles",
        "tasks",
        "linewise",
        "show",
        "password",
        "key_filename",
        "abort_on_prompts",
        "skip_unknown_tasks",
        "reject_unknown_hosts",
        "skip_bad_hosts",
        "use_ssh_config",
        "roledefs",
        "gateway",
        "gss_auth",
        "keepalive",
        "eagerly_disconnect",
        "rcfile",
        "path_behavior",
        "hide",
        "sudo_prefix",
        "lcwd",
        "no_agent",
        "forward_agent",
        "remote_interrupt",
        "port",
        "shell",
        "version",
        "use_exceptions_for",
        "connection_attempts",
        "hosts",
        "gss_deleg",
        "cwd",
        "abort_exception",
        "real_fabfile",
        "passwords",
        "sudo_password",
        "host_string",
        "shell_env",
        "always_use_pty",
        "colorize_errors",
        "exclude_hosts",
        "all_hosts",
        "sudo_prompt",
        "again_prompt",
        "echo_stdin",
        "user",
        "gss_kex",
        "command_timeout",
        "path",
        "local_user",
        "combine_stderr",
        "command_prefixes",
        "dedupe_hosts",
        "warn_only",
        "no_keys",
        "sudo_passwords",
        "roles",
        "fabfile",
        "use_shell",
        "host",
        "pool_size",
        "system_known_hosts",
        "prompts",
        "output_prefix",
        "command",
        "timeout",
        "default_port",
        "ssh_config_path",
        "parallel",
        "sudo_user",
        "ok_ret_codes",
    ),
)
