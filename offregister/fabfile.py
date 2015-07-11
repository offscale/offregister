from fabric import api


def hostname():
    api.run('hostname')
