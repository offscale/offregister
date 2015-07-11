from fabric.api import run, cd

from offregister.utils import get_tempdir_fab


def ubuntu_install_flynn():
    # run('L=/usr/local/bin/flynn && curl -sSL -A "`uname -sp`" https://dl.flynn.io/cli | zcat >$L && chmod +x $L')
    run('sudo bash < <(curl -fsSL https://dl.flynn.io/install-flynn)')


def core_install_flynn():
    pass


def ubuntu_serve_flynn(dns_name):
    run('sudo flynn-host init --init-discovery=3')
    run('pgrep flynn || sudo start flynn-host')
    run('sudo CLUSTER_DOMAIN={dns_name} flynn-host bootstrap --min-hosts=3 /etc/flynn/bootstrap-manifest.json'.format(
        dns_name=dns_name
    ))
