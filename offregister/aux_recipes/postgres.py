from functools import partial
from os import path
from pkg_resources import resource_filename
from fabric.api import sudo
from fabric.contrib.files import upload_template
from offregister.aux_recipes.apt import apt_depend_factory

tpl_dir = partial(path.join, path.dirname(resource_filename('offregister.aux_recipes', '__init__.py')), 'templates')


def ubuntu_install_postgres(version='9.3', username='postgres', dbs=None, users=None,
                            extra_deps=tuple(), cluster=False, skip_apt_update=False):
    apt_depend_factory(skip_apt_update)('postgresql-{version}'.format(version=version),
                                        'postgresql-contrib-{version}'.format(version=version),
                                        'postgresql-server-dev-{version}'.format(version=version),
                                        *extra_deps)
    # sudo('service postgres {service_cmd}'.format(service_cmd=service_cmd))
    postgres = partial(sudo, user='postgres')

    def require_db(db):
        if len(postgres("psql -tAc '\l {db}'".format(db=db))) == 0:
            postgres('createdb {db}'.format(db=db))

    def require_user(user):
        if len(postgres("psql -tAc '\du {user}'".format(user=user))) == 0:
            postgres('createuser --superuser {user}'.format(user=user))

    cluster_with_pgpool2(skip_apt_update)
    return {'dbs': map(require_db, dbs), 'users': map(require_user, users)}


def cluster_with_pgpool2(template_vars=None, skip_apt_update=False):
    apt_depend_factory(skip_apt_update)('pgpool2')

    default_tpl_vars = {'PORT': '5433'}
    if not template_vars:
        template_vars = default_tpl_vars
    else:
        for k, v in default_tpl_vars.iteritems():
            if k not in template_vars:
                template_vars[k] = v

    upload_template(tpl_dir('pgpool.conf'), '/etc/pgpool2/pgpool.conf',
                    mode=640, context=template_vars, use_sudo=True)
    sudo('chown root:postgres /etc/pgpool2/pgpool.conf')
    upload_template(tpl_dir('pgpool.conf'), '/usr/share/pgpool2/pgpool.conf',
                    mode=644, context=template_vars, use_sudo=True)
    sudo('chown root:root /usr/share/pgpool2/pgpool.conf')
