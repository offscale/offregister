import json
from collections import OrderedDict
from functools import partial
from itertools import ifilter, izip, imap
from operator import add
from os import environ, path
from os import listdir
from sys import modules
from time import time

from invoke import Executor, Collection, task
from invoke.env import Environment

from offutils import update_d, get_sorted_strnum, filter_strnums, binary_search, raise_f, pp, is_sequence
from offutils_strategy_register import save_node_info

from offregister import root_logger
from offregister.drivers import OffregisterBaseDriver, PreparedClusterObj
from offregister.utils import guess_os, get_pip_packages, pip_install


@task
def hello(ctx):
    print("Hello, world!")
    return 'done'


class OffInvoke(OffregisterBaseDriver):
    func_names = None

    def __init__(self, env_obj, node, node_name, dns_name):
        super(OffInvoke, self).__init__(env_obj, node, node_name, dns_name)
        # env.update({k: getattr(env_obj, k) for k in dir(env_obj) if getattr(env_obj, k) is not None})

    def prepare_cluster_obj(self, cluster, res):
        pass

    def run_tasks(self, cluster_path, cluster_type, cluster_args, cluster_kwargs, res, tag):
        # Define and configure root namespace
        # ===================================

        # NOTE: `namespace` or `ns` name is required!
        namespace = Collection(
            hello,
            # put tasks or nested collections here
        )

        def invoke_execute(context, command_name, **kwargs):
            """
            Helper function to make invoke-tasks execution easier.
            """
            results = Executor(namespace, config=context.config).execute((command_name, kwargs))
            target_task = context.root_namespace[command_name]
            return results[target_task]

        namespace.configure({
            'root_namespace': namespace,
            'invoke_execute': invoke_execute,
        })
        pass

    def prepare_cluster_obj(self, cluster, res):
        cluster_args = cluster['args'] if 'args' in cluster else tuple()
        cluster_kwargs = update_d({
            'domain': self.dns_name,
            'node_name': self.node_name,
            'public_ipv4': self.node.public_ips[-1],
            'cache': {},
            'cluster_name': cluster.get('cluster_name')
        }, cluster['kwargs'] if 'kwargs' in cluster else {})
        cluster_type = cluster['module'].replace('-', '_')
        cluster_path = '/'.join(ifilter(None, (cluster_type, cluster_kwargs['cluster_name'])))
        cluster_kwargs.update(cluster_path=cluster_path)
        if 'cache' not in cluster_kwargs:
            cluster_kwargs['cache'] = {}

        if ':' in cluster_type:
            cluster_type, _, tag = cluster_type.rpartition(':')
            del _
        else:
            tag = None

        cluster_kwargs.update(tag=tag)

        if tag == 'master':
            cluster_kwargs.update(master=True)
        if hasattr(self.node, 'private_ips') and len(self.node.private_ips):
            cluster_kwargs.update(private_ipv4=self.node.private_ips[-1])

        guessed_os = guess_os(node=self.node)

        # import `cluster_type`
        try:
            setattr(self, 'fab', getattr(__import__(cluster_type, globals(), locals(), [guessed_os], -1), guessed_os))
        except AttributeError as e:
            if e.message != "'module' object has no attribute '{os}'".format(os=guessed_os):
                raise
            raise ImportError('Cannot `import {os} from {cluster_type}`'.format(os=guessed_os,
                                                                                cluster_type=cluster_type))
        fab_dir = dir(self.fab)

        # Sort functions like so: `step0`, `step1`
        func_names = get_sorted_strnum(fab_dir)
        func_names = self.filter_funcs(cluster, func_names)


        self.func_names = func_names

        return PreparedClusterObj(cluster_path=cluster_path, cluster_type=cluster_type,
                                  cluster_args=cluster_args, cluster_kwargs=cluster_kwargs,
                                  res=res, tag=tag)
    """
    def run_tasks(self, cluster_path, cluster_type, cluster_args, cluster_kwargs, res, tag):
        for idx, step in enumerate(self.func_names):
            kw_args = cluster_kwargs.copy()  # Only allow mutations on cluster_kwargs.cache [between task runs]
            kw_args['cache'] = cluster_kwargs['cache']  # ref
            t = time()
            exec_output = execute(getattr(self.fab, step), *cluster_args, **kw_args)[self.dns_name]

            if idx == 0:
                if self.dns_name not in res:
                    res[self.dns_name] = {cluster_path: OrderedDict({step: {t: exec_output}})}
                if tag == 'master':
                    save_node_info('master', [self.node_name], folder=cluster_type, marshall=json)

            if cluster_path not in res[self.dns_name]:
                res[self.dns_name][cluster_path] = OrderedDict({step: OrderedDict({t: exec_output})})
            elif step not in res[self.dns_name][cluster_path]:
                res[self.dns_name][cluster_path][step] = OrderedDict({t: exec_output})
            else:
                res[self.dns_name][cluster_path][step][t] = exec_output

            if res[self.dns_name][cluster_path][step] and '_merge' in res[self.dns_name][cluster_path][step]:
                merge = res[self.dns_name][cluster_path][step].pop('_merge')
                self.merge_steps(merge, res)

            if '_merge' in cluster_kwargs['cache']:
                merge = cluster_kwargs['cache'].pop('_merge')
                self.merge_steps(merge, res)

            if 'offregister_fab_utils' in res[self.dns_name]:
                del res[self.dns_name]['offregister_fab_utils']

    def merge_steps(self, merge, res):
        for (mod, step_name), out in merge.iteritems():
            mod = mod.partition('.')[0]
            if mod not in res[self.dns_name]:
                res[self.dns_name][mod] = {}
            if step_name not in res[self.dns_name][mod]:
                res[self.dns_name][mod][step_name] = out
            else:
                res[self.dns_name][mod][step_name].update(out)

    '''
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
    '''
    """

    @staticmethod
    def filter_funcs(cluster, func_names):
        if 'run_cmds' not in cluster:
            return func_names

        if 'exclude' in cluster['run_cmds']:
            func_names = tuple(ifilter(lambda func: func not in cluster['run_cmds']['exclude'], func_names))

        '''run_cmds_type = type(cluster['run_cmds'])
                {DictType: filter_by(cluster['run_cmds'], func_names)
           }.get(run_cmds_type, raise_f(NotImplementedError, '{!s} unexpected for run_cmds'.format(run_cmds_type)))'''

        return tuple(filter_strnums(cluster['run_cmds'].get('op'), cluster['run_cmds']['val'], func_names))

    @staticmethod
    def handle_deprecations(func_names):
        called = 0
        deprecated = lambda: add(called, 1) and called == 0 and root_logger.warn(
            'Depreciation: use function names ending in numerals instead')
        deprecated_func_names = 'install', 'setup', 'serve', 'start'

        frozenset(func_name for func_name in deprecated_func_names
                  if binary_search(func_names, func_name) > -1 and deprecated()
                  ) and next((func_name for func_name in func_names
                              if str.isdigit(func_name[1])), False) and deprecated()

    @staticmethod
    def install_packages(cluster):
        from offregister import recipes

        dash_un_cluster = cluster['module'].replace('-', '_')

        pip_packages = get_pip_packages()
        available_recipes = frozenset(ifilter(lambda s: not s.startswith('_'), dir(recipes)))
        loaded_modules = frozenset(imap(lambda name: modules[name], frozenset(modules) & frozenset(globals())))

        mods = available_recipes | loaded_modules
        # Ensure package required to install cluster is available
        if cluster['module'] not in mods and dash_un_cluster not in mods:
            if cluster['module'] in pip_packages:
                # import
                pass
            elif dash_un_cluster in pip_packages:
                # import
                pass
            else:
                # `folder` is one above `offregister` directory
                folder = environ.get('PKG_DIR', path.dirname(path.dirname(path.dirname(__file__))))

                ls_folder = listdir(folder)
                pip_install_d = partial(pip_install, options_attr={'src_dir': folder})
                if cluster['module'] in ls_folder:
                    pip_install_d(path.join(folder, cluster['module']))
                elif dash_un_cluster in ls_folder:
                    pip_install_d(path.join(folder, dash_un_cluster))
                else:
                    raise ImportError("Cannot find package for cluster: '{!s}'".format(cluster['module']))
