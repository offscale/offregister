# -*- coding: utf-8 -*-
def hostname(c):
    """
    :param c: Connection
    :type c: ```fabric.connection.Connection```
    """
    c.run("hostname")
