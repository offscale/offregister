# Taiga roadmap

## General

  - Extract into own python package, host on pypi, and decouple from off* projects
  - After ^, maybe also provide `fabfile`s for the taiga-front and taiga-back repositories
  - Push all non-cache related configuration into a YAML file
  - Add configuration around postgres (e.g.: to set it up in a separate cluster, or to use DBaaS one)

## Production

  - Consider packaging virtualenv into deb; with dh-virtualenv; to facilitate quicker bootstrapping
  - Integrate log aggregation and monitoring
  - Worry about permissions, modes and ownership [e.g.: starting with no more perverse use of `$HOME`!]
  - HA: clustering, pooling and load-balancing
  - Document in a quick-start guide how to setup:
    - 1 node
    - 2 nodes (1 db, 1 app)
    - 3 node cluster
    - 2x3 node clusters (1 db, 1 app)
  - RabbitMQ and Redis + their clusters [does Taiga use it, or is this on their Roadmap?]
  - SMTP server + related clustering [more offregister roadmap than Taiga... but still!]
