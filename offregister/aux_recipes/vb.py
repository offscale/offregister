from fabric.api import run, sudo
from fabric.contrib.files import append

from offregister_fab_utils.apt import apt_depends


def ubuntu_install_vb(extensions=False, distribution='trusty'):
    apt_depends('curl')
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
    apt_depends('virtualbox-5.0' 'dkms')

    if extensions:
        raise NotImplementedError()
