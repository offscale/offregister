from offregister_fab_utils.apt import apt_depends


def ubuntu_install_mesos(c, version="0.27.0", apt_update=True, *args, **kwargs):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    apt_depends(
        c,
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
    c.run(
        "curl -O http://www.apache.org/dist/mesos/{version}/mesos-{version}.tar.gz".format(
            version=version
        )
    )
    c.run("tar -zxf mesos-{version}.tar.gz".format(version=version))


def core_install_mesos(c, *args, **kwargs):
    raise NotImplementedError()


def ubuntu_serve_mesos(c, *args, **kwargs):
    raise NotImplementedError()


def core_serve_mesos(c, *args, **kwargs):
    raise NotImplementedError()
