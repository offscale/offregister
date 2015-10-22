from itertools import ifilter, imap
from operator import methodcaller

from fabric.api import run, cd

from offutils import it_consumes
from offregister.utils import get_tempdir_fab
from offregister.aux_recipes import base


def ubuntu_install_flynn(*args, **kwargs):
    # run('L=/usr/local/bin/flynn && curl -sSL -A "`uname -sp`" https://dl.flynn.io/cli | zcat >$L && chmod +x $L')
    run('sudo bash < <(curl -fsSL https://dl.flynn.io/install-flynn)')
    it_consumes(imap(lambda e: methodcaller(e)(base), ifilter(lambda a: a.startswith('ubuntu_'), dir(base))))


def core_install_flynn(*args, **kwargs):
    raise NotImplementedError('Flynn not [yet?] implemented on CoreOS')


def ubuntu_serve_flynn(*args, **kwargs):
    print 'kwargs =', kwargs
    run('sudo flynn-host init --init-discovery=3')
    run('pgrep flynn || sudo start flynn-host')
    '''
    run('sudo CLUSTER_DOMAIN={dns_name} flynn-host bootstrap --min-hosts=3 /etc/flynn/bootstrap-manifest.json'.format(
        dns_name=dns_name
    ))
    '''
