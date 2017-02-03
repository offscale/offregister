from abc import ABCMeta, abstractmethod
from collections import namedtuple, OrderedDict

from libcloud.compute.base import Node
from offutils import is_sequence

from offregister.process_node import Env

PreparedClusterObj = namedtuple('PreparedClusterObj', ('cluster_path', 'cluster_type', 'cluster_args', 'cluster_kwargs',
                                                 'res', 'tag'))


class OffregisterBaseDriver(object):
    __metaclass__ = ABCMeta

    def __init__(self, env_namedtuple, node, node_name, dns_name):
        """
        OffregisterBaseDriver: base driver for implementing support for configuration managers

        :keyword env_namedtuple: Env (same as fabric.api.env)
        :type env_namedtuple: ``Env``

        :keyword node: Node
        :type node: ``Node``

        :keyword node_name: name of node
        :type node_name: ``str``

        :keyword dns_name: DNS name associated with node
        :type dns_name: ``str``
        """
        self.env_namedtuple = env_namedtuple
        self.node = node
        self.node_name = node_name
        self.dns_name = dns_name

    @abstractmethod
    def prepare_cluster_obj(self, cluster, res):
        """

        :keyword cluster: a dictionary
        :type cluster: ``{}``

        cluster contains something like:
            {"cluster_name": "odoo0", "args": [], "kwargs": {}, "module": "offregister-odoo", "type": "fabric"}

        :keyword res: a dictionary
        :type res: ``{}``

        :return: PreparedClusterObj, i.e.: cluster_path, cluster_type, res, tag, args, kwargs
        :rtype: ``PreparedClusterObj``
        """

    @abstractmethod
    def run_tasks(self, cluster_path, cluster_type, cluster_args, cluster_kwargs, res, tag):
        """

        :keyword cluster_path: cluster_path
        :type cluster_path: ``str``

        :keyword cluster_type: cluster_type
        :type cluster_type: ``str`

        :keyword res: res
        :type res: ``{}``

        :keyword tag: tag
        :type tag: ``str`

        :keyword cluster_args: args
        :type cluster_args: ``[]``

        :keyword cluster_kwargs: kv
        :type cluster_kwargs: ``{}``
        """

    @staticmethod
    @abstractmethod
    def install_packages(cluster):
        """
        :keyword cluster: dictionary of the cluster object in the register key of the conf
        :type cluster: ``{}``

        """

    def add_to_res(self, res, cluster_path, step, exec_output):
        # TODO: generalise
        if cluster_path not in res[self.dns_name]:
            res[self.dns_name][cluster_path] = OrderedDict(**{step: exec_output})
        elif step not in res[self.dns_name][cluster_path]:
            res[self.dns_name][cluster_path][step] = exec_output
        else:
            if not is_sequence(res[self.dns_name][cluster_path][step]):
                res[self.dns_name][cluster_path][step] = [res[self.dns_name][cluster_path][step]]
            if not isinstance(res[self.dns_name][cluster_path][step], list):
                res[self.dns_name][cluster_path][step] = list(res[self.dns_name][cluster_path][step])
            res[self.dns_name][cluster_path][step].append(exec_output)