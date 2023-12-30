from abc import ABCMeta, abstractmethod
from collections import OrderedDict, namedtuple
from sys import version_info

from offutils import is_sequence


# From `six` 1.15.0
def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""

    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class metaclass(type):
        def __new__(mcs, name, this_bases, d):
            if version_info[:2] >= (3, 7):
                from types import resolve_bases

                # This version introduced PEP 560 that requires a bit
                # of extra care (we mimic what is done by __build_class__).
                resolved_bases = resolve_bases(bases)
                if resolved_bases is not bases:
                    d["__orig_bases__"] = bases
            else:
                resolved_bases = bases
            return meta(name, resolved_bases, d)

        @classmethod
        def __prepare__(cls, name, this_bases):
            return meta.__prepare__(name, bases)

    return type.__new__(metaclass, "temporary_class", (), {})


PreparedClusterObj = namedtuple(
    "PreparedClusterObj",
    ("cluster_path", "cluster_type", "cluster_args", "cluster_kwargs", "res", "tag"),
)


class OffregisterBaseDriver(with_metaclass(ABCMeta, object)):
    def __init__(self, env, node, node_name, dns_name):
        """
        OffregisterBaseDriver: base driver for implementing support for configuration managers

        :keyword env: Env
        :type env: ```Env```

        :keyword node: Node
        :type node: ```Node```

        :keyword node_name: name of node
        :type node_name: ```str```

        :keyword dns_name: DNS name associated with node
        :type dns_name: ```str```
        """
        self.env_namedtuple = env
        self.node = node
        self.node_name = node_name
        self.dns_name = dns_name

    @abstractmethod
    def prepare_cluster_obj(self, cluster, res):
        """

        :keyword cluster: e.g., {"cluster_name": "odoo0", "args": [], "kwargs": {}, "module": "offregister-odoo", "type": "fabric"}
        :type cluster: ```dict```

        :keyword res: a dictionary
        :type res: ```dict```

        :return: PreparedClusterObj, i.e.: cluster_path, cluster_type, res, tag, args, kwargs
        :rtype: ```PreparedClusterObj```
        """

    @abstractmethod
    def run_tasks(
        self, cluster_path, cluster_type, cluster_args, cluster_kwargs, res, tag
    ):
        """

        :keyword cluster_path: cluster_path
        :type cluster_path: ```str```

        :keyword cluster_type: cluster_type
        :type cluster_type: ```str```

        :keyword res: res
        :type res: ```dict```

        :keyword tag: tag
        :type tag: ```str```

        :keyword cluster_args: args
        :type cluster_args: ```List[any]```

        :keyword cluster_kwargs: kv
        :type cluster_kwargs: ```dict```
        """

    @staticmethod
    @abstractmethod
    def install_packages(cluster):
        """
        :keyword cluster: dictionary of the cluster object in the register key of the conf
        :type cluster: ```dict```

        """

    def add_to_res(self, res, cluster_path, step, exec_output):
        # TODO: generalise
        if cluster_path not in res[self.dns_name]:
            res[self.dns_name][cluster_path] = OrderedDict(**{step: exec_output})
        elif step not in res[self.dns_name][cluster_path]:
            res[self.dns_name][cluster_path][step] = exec_output
        else:
            if not is_sequence(res[self.dns_name][cluster_path][step]):
                res[self.dns_name][cluster_path][step] = [
                    res[self.dns_name][cluster_path][step]
                ]
            if not isinstance(res[self.dns_name][cluster_path][step], list):
                res[self.dns_name][cluster_path][step] = list(
                    res[self.dns_name][cluster_path][step]
                )
            res[self.dns_name][cluster_path][step].append(exec_output)
