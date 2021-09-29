#!/usr/bin/env python

"""
CLI entrypoint
"""

from __future__ import print_function

import json
import pprint
import textwrap
from argparse import ArgumentParser
from os import path
from pprint import pprint
from subprocess import CalledProcessError
from sys import stdout, version_info

from offutils_strategy_register import fetch_node, list_nodes
from pkg_resources import resource_filename

from .__init__ import __version__, root_logger
from .process_node import ProcessNode

if version_info[0] == 3:
    from io import StringIO
    from itertools import filterfalse
else:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
    from itertools import ifilterfalse as filterfalse


def _build_parser():
    """
    Parser constructing function

    :return: instanceof ArgumentParser
    :rtype: ```ArgumentParser```
    """
    parser = ArgumentParser(
        prog="python -m offregister",
        description="Register node to cluster(s). Node is found by manual specification, or popped from a queue.",
        epilog="Example usage: %(prog)s -q etcd -r mesos:location -r etcd:location -r consul:location",
    )
    parser.add_argument("-d", "--dns", help="DNS for node (if no queue)")
    parser.add_argument("-i", "--ip", help="Public IP for node (if no queue)")
    parser.add_argument(
        "-q", "--queue", help='Type of queue. Default: "etcd"', default="etcd"
    )
    parser.add_argument(
        "-l",
        "--queue-location",
        help='Location of queue. Default: "http://localhost:2379"',
        default="http://localhost:2379",
    )
    parser.add_argument(
        "-r",
        "--register",
        nargs="+",
        help="Join node to which cluster(s). Example: mesos:location, etcd:location",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Schema file. Can use the same one across all off- CLIs.",
        default=path.join(
            path.dirname(resource_filename("offregister", "__main__.py")),
            "_config",
            "register.sample.json",
        ),
    )
    parser.add_argument(
        "-w",
        "--within",
        help="Clusters to set nodes within [/unclustered/* (from .json conf)]",
    )
    parser.add_argument(
        "-m",
        "--method",
        help="Method to run. E.g.: `tail` or `set_clusters`. [set_clusters]",
        default="set_clusters",
    )
    parser.add_argument(
        "-a",
        "--method-args",
        help='Method args. Use with --method. Example: "-f -n 20"',
        default=tuple(),
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s {}".format(__version__)
    )
    return parser


def process_within(register_within, config, method, method_args):
    """
    Helper function to process a collection of tasks from a dictionary

    :param register_within: List of clusters to register the node's operation to
    :type register_within: ```Iterable[str]```

    :param config: dictionary for config
    :type config: ```dict```

    :param method: Which method to run
    :type method: ```str```

    :param method_args: Arguments to provide to the function by the `method` name
    :type method_args: ```Tuple[str]```
    """
    if not len(register_within):
        raise Exception("No clusters found to join this node to")

    for cluster_location in register_within:
        if cluster_location.endswith("*"):
            cluster_location = cluster_location[:-2]
        ProcessNode.validate_conf(config, cluster_location)
        process_nodes(cluster_location, config, method, method_args)


# From https://stackoverflow.com/a/4303996
def pprint_OrderedDict(object, **kwrds):
    """
    Pretty print an OrderedDict

    :param object: Input container
    :type object: ```OrderedDict```

    :param kwrds: Keyword arguments
    :type kwrds: ```dict```
    """
    try:
        width = kwrds["width"]
    except KeyError:  # unlimited, use stock function
        pprint(object, **kwrds)
        return
    buffer = StringIO()
    stream = kwrds.get("stream", stdout)
    kwrds.update({"stream": buffer})
    pprint(object, **kwrds)
    words = buffer.getvalue().split()
    buffer.close()

    print(textwrap.fill(" ".join(words), width=width), file=stream)


def process_nodes(cluster_location, config, method, method_args):
    """
    Helper function that runs methods against cluster location with given config

    :param cluster_location: Cluster to register the node's operation to
    :type cluster_location: ```str```

    :param config: dictionary for config
    :type config: ```dict```

    :param method: Which method to run
    :type method: ```str```

    :param method_args: Arguments to provide to the function by the `method` name
    :type method_args: ```Tuple[str]```
    """
    clustering_results = []
    nodes = list_nodes(cluster_location, marshall=json)
    if len(nodes) == 0:
        try:
            nodes = (fetch_node(cluster_location),)  # try exact match
        except StopIteration:
            raise AssertionError("No node found at {!r}".format(cluster_location))
    assert len(nodes), "No nodes found at {!r}".format(cluster_location)
    for node_res in nodes:
        try:
            process_node_obj = ProcessNode(config, node_res, clustering_results)
            getattr(process_node_obj, method)(cluster_location, *method_args)
            clustering_results = process_node_obj.previous_clustering_results
        except CalledProcessError as e:
            root_logger.exception(e)

    pprint_OrderedDict(clustering_results)


if __name__ == "__main__":
    args = _build_parser().parse_args()
    process_node = ProcessNode(args.config)

    process_within(
        args.within
        or {
            k: process_node.process_dict["register"][k]
            for k in filterfalse(
                lambda key: key.startswith("_"), process_node.process_dict["register"]
            )
        },
        config=args.config,
        method=args.method,
        method_args=args.method_args,
    )
