from functools import partial
from os import path

from fabric.api import run, cd, put, sudo, prefix, shell_env
from fabric.contrib.files import exists
from pkg_resources import resource_filename

from offregister.aux_recipes.apt import apt_depend_factory, download_and_install
from offregister.aux_recipes.circus import ubuntu_install_circus
from offregister.aux_recipes.git import clone_or_update
from offregister.aux_recipes.nginx import ubuntu_install_nginx
from offregister.aux_recipes.postgres import ubuntu_install_postgres
from offregister.aux_recipes.python_utils import mkvirtualenv_if_needed_factory

taiga_dir = partial(path.join, path.dirname(resource_filename('offregister.aux_recipes', '__init__.py')), 'taiga')


def ubuntu_install_taiga_frontend(skip_apt_update=False):
    apt_depend_factory(skip_apt_update)('git')
    remote_home = run('printf $HOME', quiet=True)

    with cd(remote_home):
        repo = 'taiga-front'
        clone_or_update(team='taigaio', repo=repo)
        # Compile it here if you prefer
        if not exists('taiga-front/dist'):
            clone_or_update(team='taigaio', repo='taiga-front-dist')
            run('ln -s $HOME/taiga-front-dist/dist $HOME/taiga-front/dist')
        js_conf_dir = '/'.join((repo, 'dist', 'js'))
        if not exists('/'.join((js_conf_dir, 'conf.json'))):
            run('mkdir -p {conf_dir}'.format(conf_dir=js_conf_dir))
            put(taiga_dir('conf.json'), js_conf_dir)

    ubuntu_install_nginx(taiga_dir('taiga.nginx.conf'), taiga_dir('nginx.conf'),
                         name='taiga', template_vars={'HOME': remote_home})


def ubuntu_install_taiga_backend(skip_apt_update=False, database=True, database_uri=None):
    if database:
        if not exists('$HOME/.setup/postgresql'):
            run('mkdir -p $HOME/.setup')
            run('touch $HOME/.setup/postgresql')
        remote_user = run('printf $USER')
        ubuntu_install_postgres(dbs=('taiga', remote_user), users=(remote_user,))
    elif not database_uri:
        raise ValueError('Must create database or provide database_uri')

    apt_depend_factory(skip_apt_update)('git')
    with cd(run('printf $HOME')):
        ubuntu_install_python_taiga_deps(clone_or_update(team='taigaio', repo='taiga-back'))


def ubuntu_install_python_taiga_deps(cloned_xor_updated, skip_apt_update=False):
    remote_home = run('printf $HOME')
    apt_depend_factory(skip_apt_update)(
            'python3', 'python3-pip', 'python-dev', 'python3-dev', 'python-pip',
            'virtualenvwrapper', 'libxml2-dev', 'libxslt1-dev', 'gettext', 'libgettextpo-dev'
    )

    if not run("dpkg-query --showformat='${Version}' --show python3-lxml") == '3.5.0-1':
        download_and_install(url_prefix='https://launchpad.net/ubuntu/+source/lxml/3.5.0-1/+build/8393479/+files/',
                             packages=('python3-lxml_3.5.0-1_amd64.deb',))

    with shell_env(WORKON_HOME=run('printf $HOME/.virtualenvs')), prefix(
            'source /usr/share/virtualenvwrapper/virtualenvwrapper.sh'):
        mkvirtualenv_if_needed_factory('-p /usr/bin/python3.4 --system-site-packages')('taiga')

        with prefix('workon taiga'), cd('taiga-back'):
            run("sed -i '0,/lxml==3.5.0b1/s//lxml==3.5.0/' requirements.txt")
            run('pip install -r requirements.txt')

            if cloned_xor_updated == 'cloned':
                put(taiga_dir('django.settings.py'), 'settings/local.py')
                run('python manage.py migrate --noinput')
                run('python manage.py compilemessages')
                run('python manage.py collectstatic --noinput')
                run('python manage.py loaddata initial_user')
                run('python manage.py loaddata initial_project_templates')
                run('python manage.py loaddata initial_role')
                run('python manage.py sample_data')
                ubuntu_install_circus(template_vars={'HOME': remote_home, 'USER': run('printf $USER')},
                                      local_tpl_dir=taiga_dir())
            else:
                run('python manage.py migrate --noinput')
                run('python manage.py compilemessages')
                run('python manage.py collectstatic --noinput')
                sudo('service circus restart')


def ubuntu_install_taiga(*args, **kwargs):
    put(taiga_dir('locale'), '/etc/default/locale', use_sudo=True)
    run('mkdir -p $HOME/logs')
    ubuntu_install_taiga_frontend()
    ubuntu_install_taiga_backend()


def core_install_taiga(*args, **kwargs):
    raise NotImplementedError()


def ubuntu_serve_taiga(*args, **kwargs):
    pass  # Their bootstrap script serves it also


def core_serve_taiga(*args, **kwargs):
    raise NotImplementedError()
