import json
import recipes

from os import name as os_name, environ, path, listdir
from sys import modules
from pkg_resources import resource_filename
from itertools import ifilter, imap
from functools import partial
from types import NoneType

from libcloud import security
from libcloud.compute.providers import get_driver, DRIVERS
from fabric.api import execute, env

from offutils import pp, percent_overlap, update_d

from offutils_strategy_register import list_nodes, get_node_info, node_to_dict, save_node_info, fetch_node

from offconf import replace_variables

from __init__ import logger
from utils import get_pip_packages, pip_install

pip_packages = get_pip_packages()
available_recipes = frozenset(ifilter(lambda s: not s.startswith('_'), dir(recipes)))
loaded_modules = frozenset(imap(lambda name: modules[name], frozenset(modules) & frozenset(globals())))

# AWS Certificates are acting up (on Windows), remove this in production:
if os_name == 'nt' or environ.get('disable_ssl'):
    security.VERIFY_SSL_CERT = False


class ProcessNode(object):
    def __init__(self, process_filename, node=None, previous_clustering_results=None):
        self.previous_clustering_results = previous_clustering_results
        if not node:
            node = fetch_node(marshall=json)

        with open(process_filename) as f:
            strategy = replace_variables(f.read())
        self.process_dict = json.loads(strategy)

        driver_cls = node.value['driver'] if '_' not in node.value['driver'] \
            else node.value['driver'][:node.value['driver'].find('_')
                 ] + node.value['driver'][node.value['driver'].rfind('_') + 1:]

        self.driver_name = next(driver_name for driver_name, driver_tuple in DRIVERS.iteritems()
                                if driver_tuple[1] == driver_cls)

        self.config_provider = next(provider for provider in self.process_dict['provider']['options']
                                    if provider['provider']['name'] == self.driver_name.upper())

        self.driver_name = self.driver_name.lower()

        driver = (lambda driver: driver(
            region=self.config_provider['provider']['region'],
            **self.config_provider['auth']
        ))(get_driver(self.driver_name))

        self.node_name = node.key[node.key.find('/', 1) + 1:].encode('utf8')
        if self.driver_name == 'azure':
            if 'AZURE_CLOUD_NAME' not in environ:
                raise KeyError('$AZURE_CLOUD_NAME needs to be defined. '
                               'See: http://libcloud.readthedocs.org/en/latest/compute/drivers/azure.html'
                               '#libcloud.compute.drivers.azure.AzureNodeDriver.create_node')
            nodes = driver.list_nodes(environ['AZURE_CLOUD_NAME'])
        else:
            nodes = driver.list_nodes()

        self.node = next(ifilter(lambda _node: _node.uuid == node.value['uuid'],
                                 nodes), None)
        if not self.node:
            raise EnvironmentError('node not found. Maybe the cloud provider is still provisioning?')

        if 'password' in self.node.extra:
            print 'password =', self.node.extra['password']

        # pp(node_to_dict(self.node))
        self.dns_name = self.node.extra.get('dns_name')

    @classmethod
    def validate_conf(cls, process_filename, within):
        # Init
        with open(process_filename) as f:
            process_dict = replace_variables(f.read())
        process_dict = json.loads(process_dict)

        # Ensure package required to install cluster is available
        directory = cls.get_directory(process_dict, within)
        for cluster in process_dict['register'][directory]:
            dash_un_cluster = cluster.replace('-', '_')
            mods = available_recipes | loaded_modules
            if cluster not in mods and dash_un_cluster not in mods:
                if cluster in pip_packages:
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
                    if cluster in ls_folder:
                        pip_install_d(path.join(folder, cluster))
                    elif dash_un_cluster in ls_folder:
                        pip_install_d(path.join(folder, dash_un_cluster))
                    else:
                        raise ImportError("Cannot find package for cluster: '{!s}'".format(cluster))

    def setup_connection_meta(self, within):
        if not self.node.public_ips:
            raise Exception('No public IP address, so cannot SSH')
        if self.node.state == 2:
            # state = 2 is terminated on AWS, need to lookup MAP/enum from lib for general solution. TODO
            raise Exception('Node is terminated, so cannot SSH')

        if self.driver_name == 'azure':
            env.password = self.config_provider['ssh']['node_password']
        else:
            env.key_filename = self.config_provider['ssh']['private_key_path']
            if 'password' in self.node.extra:
                env.password = self.node.extra['password']
        env.user = self.guess_os_username(self.node.driver.__class__.__name__)

        directory = self.get_directory(self.process_dict, within)
        if not self.dns_name and 'skydns2' not in self.process_dict['register'][directory] and \
                        'consul' not in self.process_dict['register'][directory]:
            self.dns_name = '{public_ip}.xip.io'.format(public_ip=self.node.public_ips[0])
            # raise Exception('No DNS name and no way of acquiring one')
        env.hosts = [self.dns_name]

    def get_directory(self, within):
        return self.get_directory(self.process_dict, within)

    @staticmethod
    def get_directory(process_dict, within):
        directory = next((directory for directory in process_dict['register']), None)
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
        directory = self.get_directory(self.process_dict, within)

        res = {}
        for cluster in self.process_dict['register'][directory]:
            self.add_to_cluster(cluster.replace('-', '_'), res)

        if self.previous_clustering_results:
            self.previous_clustering_results.update(res)
        else:
            self.previous_clustering_results = res

        return res

    def add_to_cluster(self, cluster_type, res):
        """ Specification:
          0. Search and handle `master` tag in `cluster_name`
          1. Imports `cluster_name`, seeks and sets (`install` xor `setup`) and (serve` or `start`) callables
          2. Installs `cluster_name`
          3. Serves `cluster_name`
        """
        kwargs = {
            'domain': self.dns_name,
            'node_name': self.node_name,
            'public_ipv4': self.node.public_ips[-1]
        }
        if cluster_type.endswith(':master'):
            kwargs.update(master=True)
        if hasattr(self.node, 'private_ips') and len(self.node.private_ips):
            kwargs.update(private_ipv4=self.node.private_ips[-1])

        cluster_type = cluster_type[:-len(':master')] if kwargs.get('master') else cluster_type
        guessed_os = self.guess_os()

        # import `cluster_type`
        try:
            setattr(self, 'fab', getattr(__import__(cluster_type, globals(), locals(), [guessed_os], -1), guessed_os))
        except AttributeError as e:
            if e.message != "'module' object has no attribute '{os}'".format(os=guessed_os):
                raise
            raise ImportError('Cannot `import {os} from {cluster_type}`'.format(os=guessed_os,
                                                                                cluster_type=cluster_type))
        fab_dir = set(dir(self.fab))

        install = self.fab.install if 'install' in fab_dir else self.fab.setup
        serve = self.fab.serve if 'serve' in fab_dir else self.fab.start

        res.update(execute(install, **kwargs))
        pp(node_to_dict(self.node))
        save_node_info(self.node_name, node_to_dict(self.node), folder=cluster_type, marshall=json)
        if kwargs.get('master'):
            save_node_info('masters', [self.node_name], folder=cluster_type, marshall=json)

        # etcd stuff, TODO: move
        if cluster_type == 'etcd':
            kwargs.update({'{cluster_type}_discovery'.format(cluster_type=cluster_type): next(
                ifilter(
                    None,
                    imap(lambda k: ((lambda r: r[1] if r and len(r) > 0 else None)(
                        self.previous_clustering_results.get(k, {}).get(cluster_type))
                                    if self.previous_clustering_results.get(k) else None),
                         self.previous_clustering_results)
                ),
                tuple()
            )})
        # etcd stuff, TODO: move

        res[res.keys()[0]] = {
            cluster_type: (res[res.keys()[0]], (lambda result: result[result.keys()[0]])(
                execute(serve, **kwargs)
            ))
        }

    def guess_os_username(self, hint=None):
        if hint and 'softlayer' in hint.lower():
            return 'root'

        if self.driver_name == 'azure':
            return 'azureuser'

        node_name = self.node.name.lower()
        if 'ubuntu' in node_name:
            return 'ubuntu'
        elif 'core' in node_name:
            return 'core'
        return 'user'

    def guess_os(self, hint=None):
        node_name = self.node.name.lower()
        if 'ubuntu' in node_name:
            return 'ubuntu'
        elif 'core' in node_name:
            return 'core'
        return hint or 'ubuntu'

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


handle_unprocessed = lambda: tuple(ProcessNode(resource_filename('config', 'register.sample.json'), node)
                                   for node in list_nodes(marshall=json))

if __name__ == '__main__':
    unprocessed_handler = handle_unprocessed()
    for handler in unprocessed_handler:
        pp(handler.set_clusters())
