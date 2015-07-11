from fabric.api import run


def hostname():
    return run('hostname')
