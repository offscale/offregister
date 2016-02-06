#!/usr/bin/env python

import json

from os import path
from argparse import ArgumentParser
from sys import argv
from pkg_resources import resource_filename
from itertools import ifilterfalse, imap

from offutils import pp
from offutils_strategy_register import list_nodes

from __init__ import logger
from process_node import ProcessNode


def _build_parser():
    parser = ArgumentParser(
            description='Register node to cluster(s). Node is found by manual specification, or popped from a queue.',
            epilog='Example usage: {program} -q etcd -r mesos:location, etcd:location, consul:location'.format(
                    program=argv[0])
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
    return parser


def process_within(register_within, config, method, method_args):
    if not len(register_within):
        raise Exception('No clusters found to join this node to')

    for cluster_location in register_within:
        if cluster_location.endswith('*'):
            cluster_location = cluster_location[:-2]
        ProcessNode.validate_conf(config, cluster_location)
        process_nodes(cluster_location, config, method, method_args)


def process_nodes(cluster_location, config, method, method_args):
    clustering_results = []
    for node_res in list_nodes(cluster_location, marshall=json):
        process_node_obj = ProcessNode(config, node_res, clustering_results)
        getattr(process_node_obj, method)(cluster_location, *method_args)
        clustering_results = process_node_obj.previous_clustering_results
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
