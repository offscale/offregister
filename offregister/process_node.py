import json

from pkg_resources import resource_filename, resource_string
from itertools import ifilter, imap
from functools import partial
from types import NoneType

from libcloud.compute.providers import get_driver, DRIVERS
from fabric.api import execute, env

from offutils import pp, percent_overlap, obj_to_d

from offutils_strategy_register import list_nodes, get_node_info, node_to_dict, save_node_info, fetch_node

from offconf import replace_variables

from __init__ import logger
from recipes import hostname

from recipes.consul import ubuntu_install_consul, core_install_consul
from recipes.etcd2 import ubuntu_install_etcd, core_serve_etcd, ubuntu_serve_etcd, ubuntu_tail_etcd
from recipes.mesos import ubuntu_install_mesos, core_install_mesos
from recipes.deis import ubuntu_install_deis, core_install_deis, ubuntu_serve_deis, core_serve_deis
from recipes.dokku import ubuntu_install_dokku, core_install_dokku
from recipes.flynn import ubuntu_install_flynn, core_install_flynn, ubuntu_serve_flynn
from recipes.bosh import ubuntu_install_bosh, core_install_bosh, ubuntu_serve_bosh
from recipes.coreos import ubuntu_install_coreos, core_install_coreos, ubuntu_serve_coreos, core_serve_coreos


class ProcessNode(object):
    def __init__(self, process_filename, node=None, previous_clustering_results=None):
        self.previous_clustering_results = previous_clustering_results
        if not node:
            node = fetch_node(marshall=json)

        with open(process_filename) as f:
            strategy = replace_variables(f.read())
        self.process_dict = json.loads(strategy)
        driver_name = next(driver_name for driver_name, driver_tuple in DRIVERS.iteritems()
                           if driver_tuple == tuple(node.value['driver'].rsplit('.', 1)))
        self.config_provider = None
        for driver in self.process_dict['provider']['options']:
            _driver_name = driver.keys()[0]
            if percent_overlap(driver_name.upper(), _driver_name) > 94:
                self.config_provider = driver[_driver_name]

        driver = get_driver(driver_name)(
            self.config_provider['auth']['username'], self.config_provider['auth']['key']
        )

        self.node_name = node.key[node.key.find('/', 1) + 1:].encode('utf8')
        self.node = next(ifilter(lambda _node: _node.uuid == node.value['uuid'], driver.list_nodes()), None)
        # pp(node_to_dict(self.node))
        self.dns_name = self.node.extra.get('dns_name')

    def setup_connection_meta(self, within):
        if not self.node.public_ips:
            raise Exception('No public IP address, so cannot SSH')
        if self.node.state == 2:
            # state = 2 is terminated on AWS, need to lookup MAP/enum from lib for general solution. TODO
            raise Exception('Node is terminated, so cannot SSH')
        env.key_filename = self.config_provider['ssh']['private_key_path']
        if 'password' in self.node.extra:
            env.password = self.node.extra['password']
        env.user = self.guess_os(self.node.driver.__class__.__name__)

        directory = self.get_directory(within)
        if not self.dns_name and 'skydns2' not in self.process_dict['register'][directory] and \
                        'consul' not in self.process_dict['register'][directory]:
            self.dns_name = '{public_ip}.xip.io'.format(public_ip=self.node.public_ips[0])
            # raise Exception('No DNS name and no way of acquiring one')
        env.hosts = [self.dns_name]

    def get_directory(self, within):
        directory = next((directory for directory in self.process_dict['register']), None)
        if type(directory) is NoneType or directory != within \
                and len(directory) >= len(within) + 3 or directory[-1] != '*':
            # + 3 is for /, /* and *
            raise Exception('No clusters found to join this node to')
        return directory

    def set_clusters(self, within):
        if not self.node:
            logger.warn('No node, skipping')
            return
        self.setup_connection_meta(within)
        directory = self.get_directory(within)

        res = {}
        for cluster in self.process_dict['register'][directory]:
            self.add_to_cluster(cluster, res)

        if self.previous_clustering_results:
            self.previous_clustering_results.update(res)
        else:
            self.previous_clustering_results = res

        return res

    def add_to_cluster(self, cluster_type, res):
        master = cluster_type.endswith(':master')
        kwargs = dict(master=master) if master else {}
        cluster_type = cluster_type[:-len(':master')] if master else cluster_type
        res.update(
            execute(
                globals()['{os}_install_{cluster_name}'.format(os=self.guess_os(), cluster_name=cluster_type)],
                **kwargs
            )
        )
        save_node_info(self.node_name, node_to_dict(self.node), folder=cluster_type, marshall=json)
        if master:
            save_node_info('masters', [self.node_name], folder=cluster_type, marshall=json)

        kwargs.update({'{cluster_type}_discovery'.format(cluster_type=cluster_type): next(
            ifilter(
                None,
                imap(lambda k: ((lambda r: r[1] if r and len(r) > 0 else None)(
                    self.previous_clustering_results[k][cluster_type])
                                if self.previous_clustering_results[k] else None),
                     self.previous_clustering_results)
            ),
            tuple()
        )})
        res[res.keys()[0]] = {cluster_type: (
            res[res.keys()[0]],
            (lambda result: result[result.keys()[0]])(execute(
                globals()[
                    '{os}_serve_{cluster_name}'.format(os=self.guess_os(), cluster_name=cluster_type)
                ],
                domain=self.dns_name, node_name=self.node_name, public_ipv4=self.node.public_ips[-1],
                private_ipv4=self.node.private_ips[-1], **kwargs
            ))
        )}

    def guess_os(self, hint=None):
        if hint and 'softlayer' in hint.lower():
            return 'root'
        if 'ubuntu' in self.node.name.lower():
            return 'ubuntu'
        elif 'core' in self.node.name.lower():
            return 'core'
        return 'user'

    def tail(self, within, *method_args):
        method_args = ''.join(method_args)
        self.setup_connection_meta(within)
        directory = self.get_directory(within)
        for cluster_type in self.process_dict['register'][directory]:
            cluster_type = cluster_type[:-len(':master')] if cluster_type.endswith(':master') else cluster_type
            execute(
                globals()['{os}_tail_{cluster_name}'.format(os=self.guess_os(), cluster_name=cluster_type)],
                method_args
            )


handle_unprocessed = lambda: tuple(ProcessNode(resource_filename('config', 'register.sample.json'), node)
                                   for node in list_nodes(marshall=json))

if __name__ == '__main__':
    unprocessed_handler = handle_unprocessed()
    for handler in unprocessed_handler:
        pp(handler.set_clusters())
