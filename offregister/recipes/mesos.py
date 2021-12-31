from fabric.api import run
from offregister_fab_utils.apt import apt_depends


def ubuntu_install_mesos(version="0.27.0", apt_update=True, *args, **kwargs):
    apt_depends(
        "openjdk-7-jdk",
        "build-essential",
        "python-dev",
        "python-boto",
        "curl",
        "libcurl4-nss-dev",
        "libsasl2-dev",
        "maven" "libapr1-dev",
        "libsvn-dev",
    )
    run(
        "curl -O http://www.apache.org/dist/mesos/{version}/mesos-{version}.tar.gz".format(
            version=version
        )
    )
    run("tar -zxf mesos-{version}.tar.gz".format(version=version))


def core_install_mesos(*args, **kwargs):
    raise NotImplementedError()


def ubuntu_serve_mesos(*args, **kwargs):
    raise NotImplementedError()


def core_serve_mesos(*args, **kwargs):
    raise NotImplementedError()
