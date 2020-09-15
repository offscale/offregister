from fabric.api import run


def hostname():
    run("hostname")
