# -*- coding: utf-8 -*-
from offregister_fab_utils.apt import apt_depends
from patchwork.files import append


def ubuntu_install_vb(c, extensions=False, distribution="trusty"):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    apt_depends(c, "curl")
    asc = "oracle_vbox.asc"
    c.run(
        "curl -O https://www.virtualbox.org/download/{asc}".format(asc=asc)
    )  # TODO: verify cert also
    c.sudo("apt-key add {asc}".format(asc=asc))
    append(
        "/etc/apt/sources.list",
        "deb http://download.virtualbox.org/virtualbox/debian {distribution} contrib".format(
            distribution=distribution
        ),
        use_sudo=True,
    )
    apt_depends(c, "virtualbox-5.0" "dkms")

    if extensions:
        raise NotImplementedError()
