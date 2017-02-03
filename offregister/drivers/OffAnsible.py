from collections import OrderedDict
from itertools import ifilter, imap
from collections import namedtuple

from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback.default import CallbackModule as CallbackModule_default

from offutils import update_d, it_consumes, is_sequence

from offregister import get_logger
from offregister.drivers import OffregisterBaseDriver, PreparedClusterObj

Options = namedtuple('Options',
                     ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check'])

logger = get_logger('ansible')


class OffAnsible(OffregisterBaseDriver):
    func_names = None

    def __init__(self, env_namedtuple, node, node_name, dns_name, **kwargs):
        super(OffAnsible, self).__init__(env_namedtuple, node, node_name, dns_name)
        self.driver_node_env = {
            k: getattr(env_namedtuple, k) for k in dir(env_namedtuple)
            if not k.startswith('_') and k not in ('count', 'index') and not isinstance(getattr(env_namedtuple, k),
                                                                                        property)
            }
        ansible_settings = kwargs.get('ansible_settings', {})

        # initialize needed objects
        self.variable_manager = VariableManager()
        self.loader = DataLoader()
        self.options = Options(
            **update_d(dict(connection='ssh', module_path='/path/to/mymodules', forks=100,
                            become=None, become_method=None, become_user=None, check=False),
                       ansible_settings.get('options')))

        self.passwords = update_d(dict(vault_pass='secret'), ansible_settings.get('passwords'),
                                  conn_pass=self.env_namedtuple.password if self.env_namedtuple.password else None)

        # Instantiate our ResultCallback for handling results as they come in
        self.results_callback = ResultCallback()

        # create inventory and pass to var manager
        self.inventory = Inventory(loader=self.loader, variable_manager=self.variable_manager,
                                   host_list=env_namedtuple.hosts)
        self.variable_manager.set_inventory(self.inventory)

    def prepare_cluster_obj(self, cluster, res):
        cluster_args = cluster['args'] if 'args' in cluster else tuple()
        cluster_kwargs = update_d({
            'domain': self.dns_name,
            'node_name': self.node_name,
            'public_ipv4': self.node.public_ips[-1],
            'cache': {},
            'cluster_name': cluster.get('cluster_name')
        }, cluster['kwargs'] if 'kwargs' in cluster else {})
        if 'source' in cluster:
            cluster_kwargs.update(play_source=cluster['source'])
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

        # create play with tasks
        if 'play_source' not in cluster_kwargs:
            raise NotImplementedError('Ansible from module/playbook not implemented yet. Inline your source.')
        cluster_kwargs['play_source'].update(hosts=self.env_namedtuple.hosts)
        extra_vars = {
            'ansible_host': self.env_namedtuple.host,
            'ansible_ssh_host': self.env_namedtuple.host,
            'ansible_user': self.env_namedtuple.user,
            'ansible_ssh_user': self.env_namedtuple.user,
            'ansible_port': self.env_namedtuple.port,
            'ansible_ssh_port': self.env_namedtuple.port
        }

        if 'password' in self.driver_node_env:
            extra_vars.update({'ansible_ssh_pass': self.env_namedtuple.password})
        if 'key_filename' in self.driver_node_env:
            extra_vars.update({'ansible_ssh_private_key_file': self.env_namedtuple.key_filename})
        if 'use_ssh_config' in self.driver_node_env and 'StrictHostKeyChecking' in self.env_namedtuple.use_ssh_config:
            host_key_checking = self.env_namedtuple.use_ssh_config['StrictHostKeyChecking'] == 'yes'
            extra_vars.update({
                'ansible_ssh_extra_args': '-o ' + ' -o '.join('{k}="{v}"'.format(k=k, v=v)
                                                              for k, v in
                                                              self.env_namedtuple.use_ssh_config.iteritems()
                                                              if k not in frozenset(('Port', 'User', 'Host'))),
                'ansible_host_key_checking': host_key_checking
            })

        self.variable_manager.extra_vars = extra_vars
        cluster_kwargs['play'] = Play().load(cluster_kwargs['play_source'],
                                             variable_manager=self.variable_manager,
                                             loader=self.loader)

        return PreparedClusterObj(cluster_path=cluster_path, cluster_type=cluster_type,
                                  cluster_args=cluster_args, cluster_kwargs=cluster_kwargs,
                                  res=res, tag=tag)

    def run_tasks(self, cluster_path, cluster_type, cluster_args, cluster_kwargs, res, tag):
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback=self.results_callback
            )
            tqm.run(cluster_kwargs['play'])  # returns numerical return code
            result = self.results_callback.last_result
            if 'stdout' in result:
                result = result['stdout']

            if self.dns_name not in res:
                res[self.dns_name] = OrderedDict({cluster_path: result})
            elif cluster_path in res[self.dns_name]:
                if not is_sequence(res[self.dns_name][cluster_path]):
                    res[self.dns_name][cluster_path] = [res[self.dns_name][cluster_path]]
                if not isinstance(res[self.dns_name][cluster_path], list):
                    res[self.dns_name][cluster_path] = list(res[self.dns_name][cluster_path])
                res[self.dns_name][cluster_path].append(result)
            else:
                res[self.dns_name] = OrderedDict({cluster_path: result})
        finally:
            if tqm is not None:
                tqm.cleanup()


class ResultCallback(CallbackModule_default):
    """A sample callback plugin used for performing an action as results come in

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """
    last_result = None

    @staticmethod
    def pp_lines(log, result, key, op=None, op_args=None):
        it_consumes(imap(lambda l: log.info('{host} - {l}'.format(host=result._host.name, l=l)),
                         result._result[key] if op is None else getattr(result._result[key], op)(
                             *(iter(()) if op_args is None else op_args)
                         )))

    @staticmethod
    def debug_result(location, result, *args, **kwargs):
        log = get_logger('ansible::results_callback::{}'.format(location))
        if args:
            log.info('args = {}'.format(args))
        if kwargs:
            log.info('kwargs = {}'.format(kwargs))
        if result and hasattr(result, '_result'):
            for k in result._result:
                log.info('result._result[{}] = {}'.format(k, result._result[k]))

    @staticmethod
    def error_result(location_or_log, result):
        log = get_logger('ansible::results_callback::{}'.format(location_or_log)
                         ) if isinstance(location_or_log, basestring) else location_or_log
        if 'msg' in result._result and result._result['msg']:
            ResultCallback.pp_lines(log, result, 'msg', op='split', op_args='\n')
        if 'stdout_lines' in result._result and result._result['stdout_lines']:
            ResultCallback.pp_lines(log, result, 'stdout_lines')
        if 'stderr' in result._result and result._result['stderr']:
            log.error(result._result['stderr'])

    def v2_runner_on_ok(self, result, **kwargs):
        """Print a json representation of the result

        This method could store the result in an instance attribute for retrieval later

        :keyword result: Task result
        :type result: ``ansible.executor.task_result.TaskResult``
        """
        log = get_logger('ansible.results_callback')

        if 'stdout_lines' in result._result and result._result['stdout_lines']:
            ResultCallback.pp_lines(log, result, 'stdout_lines')
            self.last_result = result._result
            # super(ResultCallback, self).v2_runner_on_ok(result)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """

        :keyword result: Task result
        :type result: ``ansible.executor.task_result.TaskResult``

        :keyword ignore_errors: whether or not to ignore errors
        :type ignore_errors: bool
        """
        assert result.is_failed()

        log = get_logger('ansible.results_callback')
        self.error_result(log, result)

    def v2_on_any(self, *args, **kwargs):
        super(ResultCallback, self).v2_on_any(*args, **kwargs)
        if args or kwargs['result']:
            self.debug_result('v2_on_any', *args, **kwargs)

    def v2_on_file_diff(self, result):
        super(ResultCallback, self).v2_on_file_diff(result)
        self.debug_result('v2_on_file_diff', result)

    def v2_playbook_on_cleanup_task_start(self, result):
        super(ResultCallback, self).v2_playbook_on_cleanup_task_start(result)
        self.debug_result('v2_playbook_on_cleanup_task_start', result)

    def v2_playbook_on_handler_task_start(self, result):
        super(ResultCallback, self).v2_playbook_on_handler_task_start(result)
        self.debug_result('v2_playbook_on_handler_task_start', result)

    '''def v2_playbook_on_import_for_host(self, result):
        super(ResultCallback, self).v2_playbook_on_import_for_host(result)
        self.debug_result('v2_playbook_on_import_for_host', result)'''

    def v2_playbook_on_include(self, result):
        super(ResultCallback, self).v2_playbook_on_include(result)
        self.debug_result('v2_playbook_on_include', result)

    '''def v2_playbook_on_no_hosts_matched(self, result):
        super(ResultCallback, self).v2_playbook_on_no_hosts_matched(result)
        self.debug_result('v2_playbook_on_no_hosts_matched', result)

    def v2_playbook_on_no_hosts_remaining(self, result):
        super(ResultCallback, self).v2_playbook_on_no_hosts_remaining(result)
        self.debug_result('v2_playbook_on_no_hosts_remaining', result)

    def v2_playbook_on_not_import_for_host(self, result):
        super(ResultCallback, self).v2_playbook_on_not_import_for_host(result)
        self.debug_result('v2_playbook_on_not_import_for_host', result)

    def v2_playbook_on_notify(self, result):
        super(ResultCallback, self).v2_playbook_on_notify(result)
        self.debug_result('v2_playbook_on_notify', result)

    def v2_playbook_on_play_start(self, result):
        super(ResultCallback, self).v2_playbook_on_play_start(result)
        self.debug_result('v2_playbook_on_play_start', result)

    def v2_playbook_on_setup(self, result):
        super(ResultCallback, self).v2_playbook_on_setup(result)
        self.debug_result('v2_playbook_on_setup', result)'''

    def v2_playbook_on_start(self, result):
        super(ResultCallback, self).v2_playbook_on_start(result)
        self.debug_result('v2_playbook_on_start', result)

    def v2_playbook_on_stats(self, result):
        super(ResultCallback, self).v2_playbook_on_stats(result)
        self.debug_result('v2_playbook_on_stats', result)

    '''def v2_playbook_on_task_start(self, result):
        super(ResultCallback, self).v2_playbook_on_task_start(result)
        self.debug_result('v2_playbook_on_task_start', result)

    def v2_playbook_on_vars_prompt(self, result):
        super(ResultCallback, self).v2_playbook_on_vars_prompt(result)
        self.debug_result('v2_playbook_on_vars_prompt', result)'''

    def v2_runner_item_on_failed(self, result):
        super(ResultCallback, self).v2_runner_item_on_failed(result)
        self.debug_result('v2_runner_item_on_failed', result)

    def v2_runner_item_on_ok(self, result):
        super(ResultCallback, self).v2_runner_item_on_ok(result)
        self.debug_result('v2_runner_item_on_ok', result)

    def v2_runner_item_on_skipped(self, result):
        super(ResultCallback, self).v2_runner_item_on_skipped(result)
        self.debug_result('v2_runner_item_on_skipped', result)

    def v2_runner_on_async_failed(self, result):
        super(ResultCallback, self).v2_runner_on_async_failed(result)
        self.debug_result('v2_runner_on_async_failed', result)

    def v2_runner_on_async_ok(self, result):
        super(ResultCallback, self).v2_runner_on_async_ok(result)
        self.debug_result('v2_runner_on_async_ok', result)

    def v2_runner_on_async_poll(self, result):
        super(ResultCallback, self).v2_runner_on_async_poll(result)
        self.debug_result('v2_runner_on_async_poll', result)

    '''def v2_runner_on_file_diff(self, result):
        super(ResultCallback, self).v2_runner_on_file_diff(result)
        self.debug_result('v2_runner_on_file_diff', result)'''

    def v2_runner_on_no_hosts(self, result):
        super(ResultCallback, self).v2_runner_on_no_hosts(result)
        self.debug_result('v2_runner_on_no_hosts', result)

    def v2_runner_on_skipped(self, result):
        super(ResultCallback, self).v2_runner_on_skipped(result)
        self.debug_result('v2_runner_on_skipped', result)

    def v2_runner_on_unreachable(self, result):
        super(ResultCallback, self).v2_runner_on_unreachable(result)
        self.error_result('v2_runner_on_unreachable', result)

    def v2_runner_retry(self, result):
        super(ResultCallback, self).v2_runner_retry(result)
        self.debug_result('v2_runner_retry', result)
