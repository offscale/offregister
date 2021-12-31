offregister
===========
[![No Maintenance Intended](http://unmaintained.tech/badge.svg)](http://unmaintained.tech)
![Python version range](https://img.shields.io/badge/python-2.7%20|%203.4%20|%203.5%20|%203.6%20|%203.7%20|%203.8%20|%203.9%20|%203.10-blue.svg)
[![License](https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT%20OR%20CC0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort)

Tool that uses JSON input to register node(s) to cluster(s). Nodes can be specified directly, or taken from `etcd`.

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

## External recipes

Install external recipes and they'll be imported automatically.
If you want them to be installed automatically:

  - set `PKG_DIR` environment variable to one level above your project, or
  - put your project one dir above offregister's

## License

Licensed under any of:

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or <https://www.apache.org/licenses/LICENSE-2.0>)
- MIT license ([LICENSE-MIT](LICENSE-MIT) or <https://opensource.org/licenses/MIT>)
- CC0 license ([LICENSE-CC0](LICENSE-CC0) or <https://creativecommons.org/publicdomain/zero/1.0/legalcode>)

at your option.

### Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall be
licensed as above, without any additional terms or conditions.
