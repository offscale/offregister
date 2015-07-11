from etcd import Client
from fabric.api import run, settings, local, sudo


def cluster_key(node_name, *clusters, **client_kwargs):
    key_name = '/unclustered/{node_name}'.format(node_name=node_name)

    client = Client(**client_kwargs)
    client.get_lock(key_name, ttl=60)
    value = client.get(key_name).value

    for cluster in clusters:
        client.set('/{cluster}/{node_name}'.format(cluster=cluster, node_name=node_name), value)

    return client.delete(key_name)


def get_tempdir_fab(run_command=run, **kwargs):
    return run("python -c 'from tempfile import gettempdir; print gettempdir()'", **kwargs)


def which_true(command, run_command=run, **kwargs):
    with settings(warn_only=True):
        installed = run_command('which {command} >/dev/null'.format(command=command), **kwargs)
    return installed.succeeded


def append_path(new_path):
    with settings(warn_only=True):
        installed = run('grep {new_path} /etc/environment'.format(new_path=new_path))

    if installed.failed:
        run('''sudo sed -e '/^PATH/s/"$/:{new_path}"/g' -i /etc/environment'''.format(
            new_path=new_path.replace('/', '\/')
        ))
