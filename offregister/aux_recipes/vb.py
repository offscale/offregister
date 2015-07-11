from fabric.api import run, sudo
from fabric.contrib.files import append


def ubuntu_install_vb(extensions=False, distribution='trusty'):
    asc = 'oracle_vbox.asc'
    run('curl -O https://www.virtualbox.org/download/{asc}'.format(asc=asc))  # TODO: verify cert also
    sudo('apt-key add {asc}'.format(asc=asc))
    append(
        '/etc/apt/sources.list',
        'deb http://download.virtualbox.org/virtualbox/debian {distribution} contrib'.format(
            distribution=distribution
        ),
        use_sudo=True
    )
    sudo('apt-get update')

    sudo('apt-get update')
    sudo('apt-get install -y virtualbox-4.3 dkms')

    if extensions:
        pass
