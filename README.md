offregister
===========

Register node(s) to cluster(s). Nodes can be specified directly, or taken from `etcd`.

## Approach

New entry in `register.sample.json`:

    "register": {
        "/unclustered/*": [
            "coreos"
            "deis"
        ]
    },
    "purpose": [
        "any-cluster"
    ],

## Usage

    usage: __main__.py [-h] [-d DNS] [-i IP] [-q QUEUE] [-l QUEUE_LOCATION]
                       [-r REGISTER [REGISTER ...]] [-c CONFIG] [-w WITHIN]
                       [-m METHOD] [-a METHOD_ARGS]
    
    Register node to cluster(s). Node is found by manual specification, or popped
    from a queue.
    
    optional arguments:
      -h, --help            show this help message and exit
      -d DNS, --dns DNS     DNS for node (if no queue)
      -i IP, --ip IP        Public IP for node (if no queue)
      -q QUEUE, --queue QUEUE
                            Type of queue. Default: "etcd"
      -l QUEUE_LOCATION, --queue-location QUEUE_LOCATION
                            Location of queue. Default: "http://localhost:2379"
      -r REGISTER [REGISTER ...], --register REGISTER [REGISTER ...]
                            Join node to which cluster(s). Example:
                            mesos:location, etcd:location
      -c CONFIG, --config CONFIG
                            Schema file. Can use the same one across all off-
                            CLIs.
      -w WITHIN, --within WITHIN
                            Clusters to set nodes within [/unclustered/* (from
                            .json conf)]
      -m METHOD, --method METHOD
                            Method to run. E.g.: `tail` or `set_clusters`.
                            [set_clusters]
      -a METHOD_ARGS, --method-args METHOD_ARGS
                            Method args. Use with --method. Example: "-f -n 20"
    
    Example usage: /usr/local/lib/python2.7/dist-packages/offregister/__main__.py
    -q etcd -r mesos:location, etcd:location, consul:location
