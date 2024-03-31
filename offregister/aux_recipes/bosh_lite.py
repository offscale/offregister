# -*- coding: utf-8 -*-
from offregister_fab_utils.apt import apt_depends


def install_bosh_lite(c):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    apt_depends(c, "git")
