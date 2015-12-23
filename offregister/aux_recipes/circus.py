from os import listdir, path
from fabric.api import run, sudo
from fabric.contrib.files import upload_template


def ubuntu_install_circus(template_vars, local_tpl_dir):
    sudo('pip2 install circus')

    for filename in listdir(local_tpl_dir):
        name, ext = path.splitext(filename)
        if name == 'circus':
            full_path = path.join(local_tpl_dir, filename)
            if ext == '.conf':
                upload_template(full_path, '/etc/init/circus.conf', context=template_vars, use_sudo=True)
            elif ext == '.ini':
                run('mkdir -p {remote_home}/conf'.format(remote_home=template_vars['HOME']))
                upload_template(full_path, '{remote_home}/conf/circus.ini'.format(remote_home=template_vars['HOME']),
                                context=template_vars)

    sudo('initctl reload-configuration')
    ''' dbus-send --system --print-reply --dest=com.ubuntu.Upstart
                  /com/ubuntu/Upstart/jobs/circus/_ org.freedesktop.DBus.Properties.GetAll string:''
                  method return sender=:1.0 -> dest=:1.726 reply_serial=2 '''
    if sudo('service circus status').endswith('stop/waiting'):
        sudo('service circus start')
    run('mkdir -p $HOME/.setup')
    run('touch $HOME/.setup/circus')
