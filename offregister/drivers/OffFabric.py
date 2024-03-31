# -*- coding: utf-8 -*-
import json
import logging
import re
from collections import OrderedDict
from functools import partial
from operator import add
from os import environ, listdir, path
from shlex import quote as shlex_quote
from sys import modules, stderr, version
from time import time

from fabric2 import Remote
from invoke import (
    AuthFailure,
    Config,
    Context,
    FailingResponder,
    Failure,
    Local,
    ResponseNotAccepted,
    StreamWatcher,
)
from six import raise_from

if version[0] == "2":
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
else:
    from io import StringIO

# import fabric.executor
import fabric.connection
from offconf import parse
from offutils import binary_search, filter_strnums, get_sorted_strnum, raise_f, update_d
from offutils.util import iteritems
from offutils_strategy_register import save_node_info

from offregister import root_logger
from offregister.drivers import OffregisterBaseDriver, PreparedClusterObj
from offregister.utils import get_pip_packages, guess_os, pip_install

logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.getLogger("offregister.utils").setLevel(logging.ERROR)


class OutputWatcher(StreamWatcher):
    def __init__(self, prefix):
        self.prefix = prefix

    def submit(self, stream):
        print("\n".join(map(partial(add, self.prefix), stream.splitlines())))
        return []


class Connection(fabric.connection.Connection):
    out_stream = StringIO()
    err_stream = StringIO()

    def run(self, command, **kwargs):
        self.out_stream = StringIO()
        self.err_stream = StringIO()
        kwargs.update({"out_stream": self.out_stream, "err_stream": self.err_stream})
        res = super(Connection, self).run(command, **kwargs)
        self._output_to_pty(**kwargs)
        return res

    def sudo(self, command, **kwargs):
        self.out_stream = StringIO()
        self.err_stream = StringIO()
        kwargs.update({"out_stream": self.out_stream, "err_stream": self.err_stream})
        res = super(Connection, self).sudo(command, **kwargs)
        self._output_to_pty(**kwargs)
        return res

    # def cd(self, command):
    #     res = super(Connection, self).cd(command, **kwargs)
    #     with connection.cd("/var/log"):
    #         prompt = connection.config.sudo.prompt
    #         connection.run(
    #             f"sudo -S -p '{prompt}' tail syslog",
    #             watchers=[SudoPasswordResponder(connection)],
    #         )

    def _sudo(self, runner, command, **kwargs):
        # TODO: See if this works https://docs.pyinvoke.org/en/stable/api/watchers.html#invoke.watchers.Responder
        prompt = self.config.sudo.prompt
        password = kwargs.pop("password", self.config.sudo.password)
        user = kwargs.pop("user", self.config.sudo.user)
        env = kwargs.get("env", {})
        # TODO: allow subclassing for 'get the password' so users who REALLY
        # want lazy runtime prompting can have it easily implemented.
        # TODO: want to print a "cleaner" echo with just 'sudo <command>'; but
        # hard to do as-is, obtaining config data from outside a Runner one
        # holds is currently messy (could fix that), if instead we manually
        # inspect the config ourselves that duplicates logic. NOTE: once we
        # figure that out, there is an existing, would-fail-if-not-skipped test
        # for this behavior in test/context.py.
        # TODO: once that is done, though: how to handle "full debug" output
        # exactly (display of actual, real full sudo command w/ -S and -p), in
        # terms of API/config? Impl is easy, just go back to passing echo
        # through to 'run'...
        user_flags = ""
        if user is not None:
            user_flags = "-H -u {} ".format(user)
        env_flags = ""
        if env:
            env_flags = "--preserve-env='{}' ".format(",".join(env.keys()))
        command = self._prefix_commands(command)
        cmd_str = "sudo -S -p '{prompt}' {env_flags}{user_flags}{command}".format(
            prompt=prompt,
            env_flags=env_flags,
            user_flags=user_flags,
            command="bash -c {}".format(shlex_quote(command)),
        )
        watcher = FailingResponder(
            pattern=re.escape(prompt),
            response="{}\n".format(password),
            sentinel="Sorry, try again.\n",
        )
        # Ensure we merge any user-specified watchers with our own.
        # NOTE: If there are config-driven watchers, we pull those up to the
        # kwarg level; that lets us merge cleanly without needing complex
        # config-driven "override vs merge" semantics.
        # TODO: if/when those semantics are implemented, use them instead.
        # NOTE: config value for watchers defaults to an empty list; and we
        # want to clone it to avoid actually mutating the config.
        watchers = kwargs.pop("watchers", list(self.config.run.watchers))
        watchers.append(watcher)
        try:
            return runner.run(cmd_str, watchers=watchers, **kwargs)
        except Failure as failure:
            # Transmute failures driven by our FailingResponder, into auth
            # failures - the command never even ran.
            # TODO: wants to be a hook here for users that desire "override a
            # bad config value for sudo.password" manual input
            # NOTE: as noted in #294 comments, we MAY in future want to update
            # this so run() is given ability to raise AuthFailure on its own.
            # For now that has been judged unnecessary complexity.
            if isinstance(failure.reason, ResponseNotAccepted):
                # NOTE: not bothering with 'reason' here, it's pointless.
                # NOTE: using raise_from(..., None) to suppress Python 3's
                # "helpful" multi-exception output. It's confusing here.
                error = AuthFailure(result=failure.result, prompt=prompt)
                raise_from(error, None)
            # Reraise for any other error so it bubbles up normally.
            else:
                raise

    def _output_to_pty(self, **kwargs):
        if kwargs.get("hide") is True and kwargs.get("echo") is not True:
            return
        prefix = "[{user}@{host}]\t".format(user=self.user, host=self.host)
        if "stdout" not in kwargs.get("hide", iter(())):
            out = self.out_stream.getvalue()
            if out:
                print("\n".join(map(partial(add, prefix), out.splitlines())))
        if "stderr" not in kwargs.get("hide", iter(())):
            err = self.err_stream.getvalue()
            if err:
                print(
                    "\n".join(map(partial(add, prefix), err.splitlines())), file=stderr
                )


class LocalWithSudo(Local):
    def __init__(self, context):
        super(LocalWithSudo, self).__init__(context)
        # Bookkeeping var for pty use case
        self.config = context.config

    def sudo(self, command, **kwargs):
        prompt = self.config.sudo.prompt
        password = kwargs.pop("password", self.config.sudo.password)
        user = kwargs.pop("user", self.config.sudo.user)
        env = kwargs.get("env", {})
        user_flags = ""
        if user is not None:
            user_flags = "-H -u {} ".format(user)
        env_flags = ""
        if env:
            env_flags = "--preserve-env='{}' ".format(",".join(env.keys()))
        # command = self._prefix_commands(command)
        cmd_str = "sudo -S -p '{prompt}' {env_flags}{user_flags}{command}".format(
            prompt=prompt,
            env_flags=env_flags,
            user_flags=user_flags,
            command="bash -c {}".format(shlex_quote(command)),
        )
        watcher = FailingResponder(
            pattern=re.escape(prompt),
            response="{}\n".format(password),
            sentinel="Sorry, try again.\n",
        )
        watchers = kwargs.pop("watchers", list(self.config.run.watchers))
        watchers.append(watcher)
        try:
            return self.run(cmd_str, watchers=watchers, **kwargs)
        except Failure as failure:
            if isinstance(failure.reason, ResponseNotAccepted):
                error = AuthFailure(result=failure.result, prompt=prompt)
                raise_from(error, None)
            else:
                raise


class OffFabric(OffregisterBaseDriver):
    func_names = None
    env = {}
    executor = None  # type: Optional[fabric.executor.Executor]
    os = None  # type: Optional[str]
    local = False

    def __init__(self, env_obj, node, node_name, dns_name):
        super(OffFabric, self).__init__(env_obj, node, node_name, dns_name)
        self.env.update(
            {
                k: getattr(env_obj, k)
                for k in dir(env_obj)
                if getattr(env_obj, k) is not None
            }
        )

    def prepare_cluster_obj(self, cluster, res):
        cluster_args = cluster["args"] if "args" in cluster else tuple()
        cluster_kwargs = update_d(
            {
                "domain": self.dns_name,
                "node_name": self.node_name,
                "public_ipv4": self.node.public_ips[-1],
                "cache": {},
                "cluster_name": cluster.get("cluster_name"),
            },
            cluster["kwargs"] if "kwargs" in cluster else {},
        )
        cluster_type = cluster["module"].replace("-", "_")
        cluster_path = "/".join(
            _f for _f in (cluster_type, cluster_kwargs["cluster_name"]) if _f
        )
        cluster_kwargs.update(cluster_path=cluster_path)
        if "cache" not in cluster_kwargs:
            cluster_kwargs["cache"] = {}

        if ":" in cluster_type:
            cluster_type, _, tag = cluster_type.rpartition(":")
            del _
        else:
            tag = None

        cluster_kwargs.update(tag=tag)

        if tag == "master":
            cluster_kwargs.update(master=True)
        if hasattr(self.node, "private_ips") and len(self.node.private_ips):
            cluster_kwargs.update(private_ipv4=self.node.private_ips[-1])

        # import `cluster_type`
        self.os = guess_os(node=self.node)
        try:
            mod = __import__(cluster_type, globals(), locals(), [self.os])
            # member_names = get_member_names(
            #     mod, predicate=lambda s: not s.startswith("_")
            # )
            # pp({"get_member_names": member_names})
            setattr(self, "fab", getattr(mod, self.os))
        except AttributeError as e:
            if not str(e).endswith("has no attribute '{os}'".format(os=self.os)):
                raise
            raise ImportError(
                "from {cluster_type} import {os}".format(
                    os=self.os, cluster_type=cluster_type
                )
            )
        fab_dir = dir(self.fab)

        # Sort functions like so: `step0`, `step1`
        func_names = get_sorted_strnum(fab_dir)
        func_names = self.filter_funcs(cluster, func_names)

        if not func_names:
            try:
                get_attr = (
                    lambda a, b: a
                    if hasattr(self.fab, a)
                    else b
                    if hasattr(self.fab, b)
                    else raise_f(AttributeError, "`{a}` nor `{b}`".format(a=a, b=b))
                )
                func_names = (get_attr("install", "setup"), get_attr("serve", "start"))
            except AttributeError as e:
                root_logger.error(
                    "{e} found in {cluster_type}".format(e=e, cluster_type=cluster_type)
                )
                raise AttributeError(
                    "Function names in {cluster_type} must end in a number".format(
                        cluster_type=cluster_type
                    )
                )  # 'must'!

            root_logger.warn(
                "Deprecation: Function names in {cluster_type} should end in a number".format(
                    cluster_type=cluster_type
                )
            )

        self.handle_deprecations(func_names)
        self.func_names = func_names

        return PreparedClusterObj(
            cluster_path=cluster_path,
            cluster_type=cluster_type,
            cluster_args=cluster_args,
            cluster_kwargs=cluster_kwargs,
            res=res,
            tag=tag,
        )

    def run_tasks(
        self, cluster_path, cluster_type, cluster_args, cluster_kwargs, res, tag
    ):
        # TODO: Use `Collection`, WiP below
        # collection = Collection()
        # for idx, step in enumerate(self.func_names):
        #     kw_args = {}
        #     print("getattr(self.fab, step):", getattr(self.fab, step), ";")
        #     collection.add_task(
        #         Task(
        #             name=step,
        #             aliases=(str(idx),),
        #             body=getattr(self.fab, step),
        #             hosts=(self.dns_name,),
        #             default=idx == 0
        #         )
        #     )
        #     # body=lambda: getattr(self.fab, step)(*cluster_args, **kw_args)))
        #
        # # hosts.value = self.dns_name
        # core_args = ParseResult(
        #     [ParserContext(args=[Argument(name="hosts", default=self.dns_name
        #                                   )])]
        # )
        #
        # self.executor = Executor(collection=collection, core=core_args)
        # # self.executor.normalize_hosts((self.dns_name,))
        #
        # self.executor.execute()

        io = StringIO()
        # config = Config(defaults={"out_stream": io})

        if self.local:
            connection = LocalWithSudo(
                Context(
                    Config(
                        {
                            "run": {"watchers": [OutputWatcher(prefix="[local]\t")]},
                            "sudo": {"password": environ["SUDO_PASSWORD"]},
                        }
                    )
                )
            )
            r = connection.run("lsb_release -rcs", hide=True)
            os_version, os_codename = r.stdout[:-1].splitlines()
            self.os = float(os_version)
        else:
            connection = Connection(self.dns_name)  # , config=config)
            connection.config.runners.remote = lambda context, inline_env: Remote(
                context=connection, inline_env=True
            )
            connection.config.out_stream = io
            # connection.config.runners.remote.inline_env = True

        cluster_kwargs["cache"]["os_version"] = self.os
        # I could use the nginxctl solution of recursive inplace modifying `map` but for now 3 levels seems sufficient
        if "NO_OFFCONF" in environ:
            kw_args = cluster_kwargs.copy()
        else:
            kw_args = {
                key: parse(val)
                if isinstance(val, str)
                else (
                    {
                        k: parse(v)
                        if isinstance(v, str)
                        else (
                            {
                                _k: (parse(_v) if isinstance(_v, str) else _v)
                                for _k, _v in iteritems(v)
                            }
                            if isinstance(v, dict)
                            else v
                        )
                        for k, v in iteritems(val)
                    }
                    if isinstance(val, dict)
                    else val
                )
                for key, val in iteritems(cluster_kwargs.copy())
            }
        # Only allow mutations on `cluster_kwargs.cache` [between task runs]
        kw_args["cache"] = cluster_kwargs["cache"]  # ref

        for idx, step in enumerate(self.func_names):
            started_at = time()
            exec_output = getattr(self.fab, step)(connection, *cluster_args, **kw_args)
            ended_at = time()

            if self.local:
                exec_stream_output = "".join(connection.stdout + connection.stderr)
            else:
                exec_stream_output = (
                    connection.out_stream.getvalue() + connection.err_stream.getvalue()
                )

            if idx == 0:
                if self.dns_name not in res:
                    res[self.dns_name] = {
                        cluster_path: OrderedDict(
                            {step: {started_at: exec_stream_output}}
                        )
                    }
                if tag == "master":
                    save_node_info(
                        "master", [self.node_name], folder=cluster_type, marshall=json
                    )

            if cluster_path not in res[self.dns_name]:
                res[self.dns_name][cluster_path] = OrderedDict(
                    {step: OrderedDict({started_at: exec_stream_output})}
                )
            elif step not in res[self.dns_name][cluster_path]:
                res[self.dns_name][cluster_path][step] = OrderedDict(
                    {started_at: exec_stream_output}
                )
            else:
                res[self.dns_name][cluster_path][step][started_at] = exec_stream_output

            res[self.dns_name][cluster_path][step][ended_at] = exec_output

            if (
                res[self.dns_name][cluster_path][step]
                and "_merge" in res[self.dns_name][cluster_path][step]
            ):
                merge = res[self.dns_name][cluster_path][step].pop("_merge")
                self.merge_steps(merge, res)

            if "_merge" in cluster_kwargs["cache"]:
                merge = cluster_kwargs["cache"].pop("_merge")
                self.merge_steps(merge, res)

            if "offregister_fab_utils" in res[self.dns_name]:
                del res[self.dns_name]["offregister_fab_utils"]

        if not self.local:
            connection.close()

    def merge_steps(self, merge, res):
        for (mod, step_name), out in iteritems(merge):
            mod = mod.partition(".")[0]
            if mod not in res[self.dns_name]:
                res[self.dns_name][mod] = {}
            if step_name not in res[self.dns_name][mod]:
                res[self.dns_name][mod][step_name] = out
            else:
                res[self.dns_name][mod][step_name].update(out)

    """
    def tail(self, within, *method_args):
        method_args = ''.join(method_args)
        self.setup_connection_meta(within)
        directory = self.get_directory(self.process_dict, within)
        for cluster_type in self.process_dict['register'][directory]:
            cluster_type = cluster_type[:-len(':master')] if cluster_type.endswith(':master') else cluster_type
            execute(
                globals()[
                    '{os}_tail_{cluster_name}'.format(os=self.guess_os_username(), cluster_name=cluster_type)],
                method_args
            )
    """

    @staticmethod
    def filter_funcs(cluster, func_names):
        if "run_cmds" not in cluster:
            return func_names

        if "exclude" in cluster["run_cmds"]:
            func_names = tuple(
                [
                    func
                    for func in func_names
                    if func not in cluster["run_cmds"]["exclude"]
                ]
            )

        """run_cmds_type = type(cluster['run_cmds'])
                {DictType: filter_by(cluster['run_cmds'], func_names)
           }.get(run_cmds_type, raise_f(NotImplementedError, '{!s} unexpected for run_cmds'.format(run_cmds_type)))"""

        if cluster["run_cmds"].get("op") == "in":
            fnames_set = frozenset(func_names)
            values_set = frozenset(cluster["run_cmds"]["val"])
            inters_set = fnames_set & values_set
            results = tuple(v for v in cluster["run_cmds"]["val"] if v in inters_set)
            if not (len(values_set) == len(cluster["run_cmds"]["val"]) == len(results)):
                root_logger.error(
                    "Expected {results} to be subset of {fnames_set}".format(
                        results=results, fnames_set=fnames_set
                    )
                )
                exit(3)
            return results

        return tuple(
            filter_strnums(
                cluster["run_cmds"].get("op"), cluster["run_cmds"]["val"], func_names
            )
        )

    @staticmethod
    def handle_deprecations(func_names):
        called = 0
        deprecated = (
            lambda: add(called, 1)
            and called == 0
            and root_logger.warn(
                "Depreciation: use function names ending in numerals instead"
            )
        )
        deprecated_func_names = "install", "setup", "serve", "start"

        frozenset(
            func_name
            for func_name in deprecated_func_names
            if binary_search(func_names, func_name) > -1 and deprecated()
        ) and next(
            (func_name for func_name in func_names if str.isdigit(func_name[1])), False
        ) and deprecated()

    @staticmethod
    def install_packages(cluster):
        from offregister import recipes

        dash_un_cluster = cluster["module"].replace("-", "_")

        pip_packages = get_pip_packages()
        available_recipes = frozenset(
            [s for s in dir(recipes) if not s.startswith("_")]
        )
        loaded_modules = frozenset(
            [modules[name] for name in frozenset(modules) & frozenset(globals())]
        )

        mods = available_recipes | loaded_modules
        # Ensure package required to install cluster is available
        if cluster["module"] not in mods and dash_un_cluster not in mods:
            if cluster["module"] in pip_packages:
                # import
                pass
            elif dash_un_cluster in pip_packages:
                # import
                pass
            else:
                # `folder` is one above `offregister` directory
                folder = environ.get(
                    "PKG_DIR",
                    path.dirname(path.dirname(path.dirname(path.dirname(__file__)))),
                )

                ls_folder = listdir(folder)
                pip_install_d = partial(pip_install, options_attr={"src_dir": folder})
                if cluster["module"] in ls_folder:
                    pip_install_d(path.join(folder, cluster["module"]))
                elif dash_un_cluster in ls_folder:
                    pip_install_d(path.join(folder, dash_un_cluster))
                else:
                    raise ImportError(
                        "Cannot find package for cluster: '{!s}'".format(
                            cluster["module"]
                        )
                    )
