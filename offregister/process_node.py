import json
from collections import namedtuple
from itertools import ifilter, imap
from os import name as os_name, environ
from sys import modules
from types import NoneType

import jsonref
from etcd import Client
from libcloud import security
from libcloud.common.vagrant import isIpPrivate
from libcloud.compute.base import Node
from libcloud.compute.providers import get_driver, DRIVERS
from libcloud.compute.types import Provider
from offutils import pp, update_d
from offutils_strategy_register import list_nodes, node_to_dict, save_node_info, KeyVal, dict_to_node
from pkg_resources import resource_filename

from __init__ import get_logger
from offregister.common.env import Env
from utils import guess_os_username, guess_os

# AWS Certificates are acting up (on Windows), remove this in production:
if os_name == 'nt' or environ.get('disable_ssl'):
    security.VERIFY_SSL_CERT = False

DirectoryFile = namedtuple('DirectoryFile', ('directory', 'file'))

logger = get_logger(modules[__name__].__name__)


class ProcessNode(object):
    node = None  # type: Node

    def __init__(self, process_filename, node=None, previous_clustering_results=None,
                 redis_client_kwargs=None):
        self.env = Env()
        self.previous_clustering_results = previous_clustering_results

        nodes = None
        if not node:
            nodes = list_nodes(marshall=json)
            node = next(n for n in nodes if 'global::' not in n.key) if len(nodes) > 1 else nodes[0]

        with open(process_filename) as f:
            self.process_dict = jsonref.load(f)

        driver_cls = node.value['driver'] if '_' not in node.value['driver'] \
            else node.value['driver'][:node.value['driver'].find('_')
                 ] + node.value['driver'][node.value['driver'].rfind('_') + 1:]

        self.driver_name = next(driver_name for driver_name, driver_tuple in DRIVERS.iteritems()
                                if driver_tuple[1].lower() in (
                                    driver_cls.lower(), "{}NodeDriver".format(driver_cls).lower()))

        self.config_provider = next(provider for provider in self.process_dict['provider']['options']
                                    if provider['provider']['name'] == (
                                        self.driver_name.upper() if hasattr(Provider, self.driver_name.upper())
                                        else next(
                                            ifilter(lambda prov_name: getattr(Provider, prov_name) == self.driver_name,
                                                    dir(Provider)))
                                    ))
        self.redis_client_kwargs = redis_client_kwargs

        self.driver_name = self.driver_name.lower()

        driver = (lambda driver: driver(
            **update_d(self.config_provider['provider'],
                       **self.config_provider.get('auth', {}))
        ))(get_driver(self.driver_name))

        self.node_name = node.key[node.key.find('/', 1) + 1:].encode('utf8')
        if nodes:
            pass
        elif self.driver_name in ('azure',):  # ('azure', 'azure_arm'):
            if 'create_with' not in self.config_provider or \
                            'ex_cloud_service_name' not in self.config_provider['create_with']:
                raise KeyError('`ex_cloud_service_name` must be defined. '
                               'See: http://libcloud.readthedocs.org/en/latest/compute/drivers/azure.html'
                               '#libcloud.compute.drivers.azure.AzureNodeDriver.create_node')
            nodes = driver.list_nodes()  # (self.config_provider['create_with']['ex_cloud_service_name'])
        elif self.driver_name == 'azure_arm':
            from libcloud.compute.drivers.azure_arm import AzureNodeDriver

            self.node = Node(node.value['uuid'],
                             node.value['name'],
                             node.value['state'],
                             node.value['public_ips'],
                             node.value['private_ips'],
                             driver=AzureNodeDriver,
                             extra=node.value['extra'])
            nodes = None
        else:
            nodes = driver.list_nodes()

        def ensure_node(n, skip_assert=False):
            if isinstance(n, KeyVal):
                n = dict_to_node(n.value) if isinstance(n.value, dict) else n.value
            elif isinstance(n, dict):
                n = dict_to_node(n)
            if not skip_assert:
                assert isinstance(n, Node)
            return n

        if self.node:
            self.node = ensure_node(self.node)
        else:
            self.node = ensure_node(next(ifilter(lambda _node: _node.value['uuid'] == node.value['uuid'], nodes), None),
                                    skip_assert=True)
            if not self.node:
                raise EnvironmentError('node not found. Maybe the cloud provider is still provisioning?')
            assert isinstance(self.node, Node)

        if self.node.extra is not None:
            if 'ssh_config' in self.node.extra:
                if 'IdentityFile' in self.node.extra['ssh_config']:
                    self.config_provider['ssh'] = {'private_key_path': self.node.extra['ssh_config']['IdentityFile']}
                    self.config_provider['ssh'].update(self.config_provider.get('ssh', {}))
                self.env.ssh_config = self.node.extra['ssh_config']
            if 'password' in self.node.extra:
                print 'password =', self.node.extra['password']
            pp(self.node.extra)

        # pp(node_to_dict(self.node))
        self.dns_name = self.node.extra.get('dns_name')

    @staticmethod
    def is_comment_cluster(cluster):
        if 'module' not in cluster:
            if '_comments' in cluster:
                return True
            else:
                raise TypeError('`module` key must be specified for each')
        return False

    @classmethod
    def validate_conf(cls, process_filename, within):
        # Init
        with open(process_filename) as f:
            process_dict = jsonref.load(f)

        def handle_cluster(cluster):
            if cls.is_comment_cluster(cluster):
                return

            if cluster['type'] == 'fabric':
                from drivers.OffFabric import OffFabric

                return OffFabric.install_packages(cluster)
            elif cluster['type'] == 'ansible':
                logger.warn('NotImplementedError: Package installation for Ansible')
                return
            else:
                raise NotImplementedError('{}'.format(cluster['type']))

        dir_or_file = ProcessNode.get_directory_or_key(process_dict, within)
        return tuple(imap(handle_cluster, process_dict['register'][
            dir_or_file.directory if dir_or_file.directory is not None else dir_or_file.file
        ]))

    def setup_connection_meta(self, within):
        if not self.node.public_ips:
            raise Exception('No public IP address, so cannot SSH')
        if self.node.state == 2:
            # state = 2 is terminated on AWS, need to lookup MAP/enum from lib for general solution. TODO
            raise Exception('Node is terminated, so cannot SSH')

        if self.node.extra is not None and 'ssh_config' in self.node.extra:
            # TODO: Get value for `self.env_kwargs['ssh_config_path']` and set that
            ssh_config_to_fab = {'IdentityFile': 'key_filename',
                                 'HostName': 'host',
                                 'Port': 'port',
                                 'User': 'user'}
            for ssh_name, fab_name in ssh_config_to_fab.iteritems():
                if ssh_name in self.node.extra['ssh_config']:
                    setattr(self.env, fab_name, self.node.extra['ssh_config'][ssh_name])

        if 'ssh' in self.config_provider:
            if 'private_key_path' in self.config_provider['ssh']:
                self.env.key_filename = self.env.key_filename or self.config_provider['ssh']['private_key_path']
            if 'node_password' in self.config_provider['ssh']:
                self.env.password = self.config_provider['ssh']['node_password']

        if self.env.user is None:
            self.env.user = self.guess_os_username()

        if self.env.password is None and 'password' in self.node.extra:
            self.env.password = self.node.extra['password']

        dir_or_key = (lambda d_or_k: d_or_k.directory or d_or_k.file)(
            ProcessNode.get_directory_or_key(self.process_dict, within)
        )

        if isIpPrivate(self.node.public_ips[0]):
            self.dns_name = self.node.public_ips[0]  # LOL
        elif not self.dns_name and 'skydns2' not in self.process_dict['register'][dir_or_key] and \
                        'consul' not in self.process_dict['register'][dir_or_key]:
            self.dns_name = self.node.public_ips[0]  # '{public_ip}.xip.io'.format(public_ip=self.node.public_ips[0])
            # raise Exception('No DNS name and no way of acquiring one')
        self.env.hosts = [self.dns_name]

    def get_directory_or_key(self, within):
        return ProcessNode.get_directory_or_key(self.process_dict, within)

    @staticmethod
    def get_directory_or_key(process_dict, within):
        directory = next((directory for directory in process_dict['register']), None)
        if type(directory) is NoneType or directory != within \
                and len(directory) >= len(within) + 3 or directory[-1] != '*':

            v = Client().read(directory).value  # Maybe pass this along?
            if v is not None:
                return DirectoryFile(directory=None, file=directory)

            # + 3 is for /, /* and *
            raise Exception('No clusters found to join this node to')

        return DirectoryFile(directory=directory, file=None)

    def set_clusters(self, within):
        if not self.node:
            logger.warn('No node, skipping')
            return
        self.setup_connection_meta(within)
        dir_or_key = ProcessNode.get_directory_or_key(self.process_dict, within)

        res = {}
        for cluster in self.process_dict['register'][dir_or_key.directory or dir_or_key.file]:
            self.add_to_cluster(cluster, res)

        if self.previous_clustering_results:
            self.previous_clustering_results.update(res)
        else:
            self.previous_clustering_results = res

        return res

    def add_to_cluster(self, cluster, res):
        """ Specification:
          0. Search and handle `master` tag in `cluster_name`
          1. Imports `cluster_name`, seeks and sets (`install` xor `setup`) and (serve` or `start`) callables
          2. Installs `cluster_name`
          3. Serves `cluster_name`
        """
        if self.is_comment_cluster(cluster):
            return

        if cluster['type'] == 'fabric':
            from drivers.OffFabric import OffFabric

            offregisterC = OffFabric
        elif cluster['type'] == 'ansible':
            from drivers.OffAnsible import OffAnsible

            offregisterC = OffAnsible
        else:
            raise NotImplementedError('{}'.format(cluster['type']))

        offregister = offregisterC(self.env, self.node, self.node_name, self.dns_name)
        add_cluster_ret = offregister.prepare_cluster_obj(cluster, res)
        offregister.run_tasks(**add_cluster_ret._asdict())
        # offregister.run_tasks(cluster_path, cluster_type, res, tag, args, kwargs)
        save_node_info(self.node_name, node_to_dict(self.node), folder=add_cluster_ret.cluster_path, marshall=json)

    def guess_os_username(self, hint=None):
        return guess_os_username(node=self.node, hint=hint)

    def guess_os(self, hint=None):
        return guess_os(node=self.node, hint=hint)


handle_unprocessed = lambda: tuple(ProcessNode(resource_filename('config', 'register.sample.json'), node)
                                   for node in list_nodes(marshall=json))

if __name__ == '__main__':
    unprocessed_handler = handle_unprocessed()
    for handler in unprocessed_handler:
        pp(handler.set_clusters('/unclustered'))
