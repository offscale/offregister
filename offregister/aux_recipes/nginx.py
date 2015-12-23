from os import path
from fabric.api import sudo, put
from fabric.contrib.files import upload_template
from offregister.aux_recipes.apt import apt_depend_factory


def ubuntu_install_nginx(local_conf_path, default_conf_path, service_cmd='restart',
                         skip_apt_update=False, name=None, template_vars=None):
    apt_depend_factory(skip_apt_update)('nginx-full')

    remote_conf_name = name or path.basename(local_conf_path).partition(path.extsep)[0]
    remote_path = '/etc/nginx/sites-available/{remote_conf_name}'.format(remote_conf_name=remote_conf_name)

    sudo('rm -f /etc/nginx/sites-enabled/{remote_conf_name}'.format(remote_conf_name=remote_conf_name))
    sudo('rm -f /etc/nginx/sites-enabled/default')
    sudo('rm -f /etc/nginx/sites-available/default')
    if template_vars:
        upload_template(local_conf_path, remote_path, context=template_vars, use_sudo=True)
    else:
        put(local_conf_path, remote_path=remote_path, use_sudo=True)
    # put(default_conf_path, '/etc/nginx/sites-enabled/default', use_sudo=True)
    sudo('ln -s /etc/nginx/sites-available/{remote_conf_name} /etc/nginx/sites-enabled/{remote_conf_name}'.format(
            remote_conf_name=remote_conf_name
    ))
    sudo('service nginx {service_cmd}'.format(service_cmd=service_cmd))
