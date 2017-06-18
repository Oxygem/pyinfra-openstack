from pyinfra.api import deploy
from pyinfra.modules import apt, files, init, server

from .util import (
    create_database,
    get_template_path,
    make_admin_env,
)


@deploy('Install identity service')
def install_identity_service(state, host):
    create_database(state, host, 'keystone')

    keystone_install = apt.packages(
        state, host,
        {'Install keystone'},
        ['keystone'],
    )

    files.template(
        state, host,
        {'Generate keystone config'},
        get_template_path('keystone.conf.j2'),
        '/etc/keystone/keystone.conf',
    )

    server.shell(
        state, host,
        {'Sync the keystone database'},
        'keystone-manage db_sync',
    )

    # Bootstrap keystone: only do this if newly installed
    if keystone_install.changed:
        server.shell(
            state, host, '''
keystone-manage fernet_setup --keystone-user keystone --keystone-group keystone
keystone-manage credential_setup --keystone-user keystone --keystone-group keystone

keystone-manage bootstrap \
     --bootstrap-password {{ host.data.admin_password }} \
    --bootstrap-admin-url http://{{ host.data.controller_host }}:35357/v3/ \
    --bootstrap-internal-url http://{{ host.data.controller_host }}:35357/v3/ \
    --bootstrap-public-url http://{{ host.data.controller_host }}:5000/v3/ \
    --bootstrap-region-id RegionOne
        ''')

    update_apache_config = files.line(
        state, host,
        {'Set ServerName in apache2 config'},
        '/etc/apache2/apache2.conf',
        'ServerName.*',
        replace='ServerName {{ host.data.ssh_hostname }}',
    )

    init.service(
        state, host,
        {'Restart apache2'},
        'apache2',
        restarted=update_apache_config.changed,
    )

    if keystone_install.changed:
        server.shell(
            state, host,
            {'Create initial projects/users/roles'},
            (
                'openstack project create --domain default service',
                'openstack project create --domain default user',
                'openstack user create --domain default --password hamble user-1',
                'openstack role create user',
                'openstack role add --project user --user user-1 user',
            ),
            env=make_admin_env(host),
        )
