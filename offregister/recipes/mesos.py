from fabric.api import run, cd, sudo

from offregister.utils import get_tempdir_fab


def ubuntu_install_mesos(version='0.25.0', apt_update=True, *args, **kwargs):
    if apt_update:
        sudo('apt-get update -qq')
    sudo('apt-get install -y openjdk-7-jdk')
    sudo('apt-get install -y build-essential python-dev python-boto libcurl4-nss-dev libsasl2-dev maven '
         'libapr1-dev libsvn-dev')
    run('curl -O http://www.apache.org/dist/mesos/{version}/mesos-{version}.tar.gz'.format(version=version))
    run('tar -zxf mesos-{version}.tar.gz'.format(version=version))


def core_install_mesos(*args, **kwargs):
    raise NotImplementedError()


def ubuntu_serve_mesos(*args, **kwargs):
    raise NotImplementedError()


def core_serve_mesos(*args, **kwargs):
    raise NotImplementedError()
