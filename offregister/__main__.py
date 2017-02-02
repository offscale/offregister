#!/usr/bin/env python
import contextlib
import json
import pprint
from collections import OrderedDict

from os import path
from argparse import ArgumentParser
from pkg_resources import resource_filename
from itertools import ifilterfalse

from offutils import pp
from offutils_strategy_register import list_nodes

from __init__ import root_logger, __version__
from process_node import ProcessNode


def _build_parser():
    parser = ArgumentParser(
        prog='python -m offregister',
        description='Register node to cluster(s). Node is found by manual specification, or popped from a queue.',
        epilog='Example usage: %(prog)s -q etcd -r mesos:location -r etcd:location -r consul:location'
    )
    parser.add_argument('-d', '--dns', help='DNS for node (if no queue)')
    parser.add_argument('-i', '--ip', help='Public IP for node (if no queue)')
    parser.add_argument('-q', '--queue', help='Type of queue. Default: "etcd"', default='etcd')
    parser.add_argument('-l', '--queue-location', help='Location of queue. Default: "http://localhost:2379"',
                        default='http://localhost:2379')
    parser.add_argument('-r', '--register', nargs='+',
                        help='Join node to which cluster(s). Example: mesos:location, etcd:location')
    parser.add_argument('-c', '--config', help='Schema file. Can use the same one across all off- CLIs.',
                        default=path.join(path.dirname(resource_filename('offregister', '__main__.py')),
                                          '_config', 'register.sample.json'))
    parser.add_argument('-w', '--within', help='Clusters to set nodes within [/unclustered/* (from .json conf)]')
    parser.add_argument('-m', '--method', help='Method to run. E.g.: `tail` or `set_clusters`. [set_clusters]',
                        default='set_clusters')
    parser.add_argument('-a', '--method-args', help='Method args. Use with --method. Example: "-f -n 20"',
                        default=tuple())
    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
    return parser


def process_within(register_within, config, method, method_args):
    if not len(register_within):
        raise Exception('No clusters found to join this node to')

    for cluster_location in register_within:
        if cluster_location.endswith('*'):
            cluster_location = cluster_location[:-2]
        ProcessNode.validate_conf(config, cluster_location)
        process_nodes(cluster_location, config, method, method_args)


@contextlib.contextmanager
def pprint_OrderedDict():
    pp_orig = pprint._sorted
    od_orig = OrderedDict.__repr__
    try:
        pprint._sorted = lambda x: x
        OrderedDict.__repr__ = dict.__repr__
        yield
    finally:
        pprint._sorted = pp_orig
        OrderedDict.__repr__ = od_orig


def process_nodes(cluster_location, config, method, method_args):
    clustering_results = []
    for node_res in list_nodes(cluster_location, marshall=json):
        process_node_obj = ProcessNode(config, node_res, clustering_results)
        getattr(process_node_obj, method)(cluster_location, *method_args)
        clustering_results = process_node_obj.previous_clustering_results

    with pprint_OrderedDict():
        pp(clustering_results)


if __name__ == '__main__':
    args = _build_parser().parse_args()
    process_node = ProcessNode(args.config)

    process_within(
        args.within or {k: process_node.process_dict['register'][k]
                        for k in ifilterfalse(lambda key: key.startswith('_'),
                                              process_node.process_dict['register'])},
        config=args.config, method=args.method, method_args=args.method_args
    )
