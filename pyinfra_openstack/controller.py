from pyinfra.api.deploy import deploy
from pyinfra.modules import apt, files, init, server

from .util import get_package_path, get_template_path

ADMIN_ENV = {
    'OS_PROJECT_DOMAIN_NAME': 'Default',
    'OS_USER_DOMAIN_NAME': 'Default',
    'OS_PROJECT_NAME': 'admin',
    'OS_USERNAME': 'admin',
    'OS_PASSWORD': 'a5db2a4d0d0b8f04668f3900e4ceddf7f60ef80a',
    'OS_AUTH_URL': 'http://controller:35357/v3',
    'OS_IDENTITY_API_VERSION': '3',
    'OS_IMAGE_API_VERSION': '2',
}


@deploy('Install controller services')
def install_controller_services(state, host):
    apt.packages(
        state, host,
        {'Install packages'},
        [
            'chrony',
            'apache2',
            'mariadb-server',
            'rabbitmq-server',
            'memcached',

            'python-memcache',
            'python-pymysql',
        ],
        latest=True,
    )

    # Chrony
    generate_chrony_config = files.template(
        state, host,
        {'Generate chrony config'},
        get_template_path('chrony-controller.conf.j2'),
        '/etc/chrony/chrony.conf',
    )

    init.service(
        state, host,
        {'Restart chrony'},
        'chrony',
        restarted=generate_chrony_config.changed,
    )

    # MariaDB
    generate_mariadb_config = files.template(
        state, host,
        {'Generate MariaDB config'},
        get_template_path('mysql.cnf.j2'),
        '/etc/mysql/mariadb.conf.d/99-openstack.cnf',
    )

    init.service(
        state, host,
        {'Restart MariadB'},
        'mysql',
        restarted=generate_mariadb_config.changed,
    )

    # RabbitMQ
    server.shell(
        state, host,
        {'Setup RabbitMQ user'},
        (
            'rabbitmqctl add_user openstack {{ host.data.rabbitmq_password }} || true',
            'rabbitmqctl set_permissions openstack ".*" ".*" ".*"',
        ),
    )

    # Memcached
    generate_memcached_config = files.template(
        state, host,
        {'Generate memcached config'},
        get_template_path('memcached.conf.j2'),
        '/etc/memcached.conf',
    )

    init.service(
        state, host,
        {'Restart memcached'},
        'memcached',
        restarted=generate_memcached_config.changed,
    )


def _create_database(state, host, database_name, name=None):
    name = name or database_name

    password = '{{ host.data.%s_password }}' % name

    server.script_template(
        state, host,
        get_package_path('scripts', 'create_database.sh.j2'),
        database=database_name,
        username=name,
        password=password,
    )


@deploy('Install identity service')
def install_identity_service(state, host):
    _create_database(state, host, 'keystone')

    keystone_install = apt.packages(
        state, host,
        {'Install keystone'},
        ['keystone'],
        latest=True,
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

    # Only do this if newly installed
    if keystone_install.changed:
        server.script_template(
            state, host,
            {'Bootstrap keystone'},
            get_package_path('scripts', 'keystone_bootstrap.sh.j2'),
        )

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
            env=ADMIN_ENV,
        )


@deploy('Install image service')
def install_image_service(state, host):
    install_glance = apt.packages(
        state, host,
        {'Install glance'},
        ['glance'],
        latest=True,
    )

    if install_glance.changed:
        _create_database(state, host, 'glance')

        server.shell(
            state, host,
            {'Create glance image user/service'},
            (
                'openstack user create --domain default --password {{ host.data.glance_password }} glance',
                'openstack role add --project service --user glance admin',
                'openstack service create --name glance image',
            ),
            env=ADMIN_ENV,
        )

        server.shell(
            state, host,
            {'Create image service endpoints'},
            (
                'openstack endpoint create --region RegionOne image public http://{{ host.data.controller_host }}:9292',  # noqa
                'openstack endpoint create --region RegionOne image internal http://{{ host.data.controller_host }}:9292',  # noqa
                'openstack endpoint create --region RegionOne image admin http://{{ host.data.controller_host }}:9292',  # noqa
            ),
            env=ADMIN_ENV,
        )

    generate_glance_api_config = files.template(
        state, host,
        {'Generate glance-api config'},
        get_template_path('glance-api.conf.j2'),
        '/etc/glance/glance-api.conf',
    )

    generate_glance_registry_config = files.template(
        state, host,
        {'Generate glance-registry config'},
        get_template_path('glance-registry.conf.j2'),
        '/etc/glance/glance-registry.conf',
    )

    server.shell(
        state, host,
        {'Sync the glance database'},
        'glance-manage db_sync',
    )

    should_restart_glance = (
        generate_glance_api_config.changed
        or generate_glance_registry_config.changed
    )

    init.service(
        state, host,
        {'Restart glance-registry'},
        'glance-registry',
        restarted=should_restart_glance,
    )

    init.service(
        state, host,
        {'Restart glance-api'},
        'glance-api',
        restarted=should_restart_glance,
    )


@deploy('Install compute service')
def install_compute_service(state, host):
    _create_database(state, host, 'nova')
    _create_database(state, host, 'nova_api', name='nova')

    install_nova = apt.packages(
        state, host,
        {'Install nova compute controller packages'},
        [
            'nova-api',
            'nova-conductor',
            'nova-consoleauth',
            'nova-novncproxy',
            'nova-scheduler',
            'nova-placement-api',
        ],
        latest=True,
    )

    if install_nova.changed:
        server.shell(
            state, host,
            {'Create nova compute user/service'},
            (
                'openstack user create --domain default --password {{ host.data.nova_password }} nova',
                'openstack role add --project service --user nova admin',
                'openstack service create --name nova compute',
            ),
            env=ADMIN_ENV,
        )

        server.shell(
            state, host,
            {'Create compute service endpoints'},
            (
                'openstack endpoint create --region RegionOne compute public http://{{ host.data.controller_host }}:8774/v2.1/%\(tenant_id\)s',  # noqa
                'openstack endpoint create --region RegionOne compute internal http://{{ host.data.controller_host }}:8774/v2.1/%\(tenant_id\)s',  # noqa
                'openstack endpoint create --region RegionOne compute admin http://{{ host.data.controller_host }}:8774/v2.1/%\(tenant_id\)s',  # noqa
            ),
            env=ADMIN_ENV,
        )

        server.shell(
            state, host,
            {'Create nova placement user/service'},
            (
                'openstack user create --domain default --password {{ host.data.placement_password }} placement',  # noqa
                'openstack role add --project service --user placement admin',
                'openstack service create --name placement placement',
            ),
            env=ADMIN_ENV,
        )

        server.shell(
            state, host,
            {'Create compute service endpoints'},
            (
                'openstack endpoint create --region RegionOne placement public http://{{ host.data.controller_host }}:8778',  # noqa
                'openstack endpoint create --region RegionOne placement internal http://{{ host.data.controller_host }}:8778',  # noqa
                'openstack endpoint create --region RegionOne placement admin http://{{ host.data.controller_host }}:8778',  # noqa
            ),
            env=ADMIN_ENV,
        )

    generate_nova_config = files.template(
        state, host,
        {'Generate nova config'},
        get_template_path('nova-controller.conf.j2'),
        '/etc/nova/nova.conf',
    )

    server.shell(
        state, host,
        {'Sync the glance database'},
        (
            'nova-manage api_db sync',
            'nova-manage db sync',
        ),
    )

    for service in (
        'nova-api',
        'nova-consoleauth',
        'nova-scheduler',
        'nova-conductor',
        'nova-novncproxy',
    ):
        init.service(
            state, host,
            {'Restart {0}'.format(service)},
            service,
            restarted=generate_nova_config.changed,
        )


@deploy('Install network service')
def install_network_service(state, host):
    _create_database(state, host, 'neutron')

    install_neutron = apt.packages(
        state, host,
        {'Install neutron network controller packages'},
        [
            'neutron-server',
            'neutron-plugin-ml2',
            'neutron-linuxbridge-agent',
            'neutron-dhcp-agent',
            'neutron-metadata-agent',
        ],
        latest=True,
    )

    if install_neutron.changed:
        server.shell(
            state, host,
            {'Create neutron network user/service'},
            (
                'openstack user create --domain default --password {{ host.data.neutron_password }} neutron',
                'openstack role add --project service --user neutron admin',
                'openstack service create --name neutron network',
            ),
            env=ADMIN_ENV,
        )

        server.shell(
            state, host,
            {'Create network service endpoints'},
            (
                'openstack endpoint create --region RegionOne network public http://{{ host.data.controller_host }}:9696',  # noqa
                'openstack endpoint create --region RegionOne network internal http://{{ host.data.controller_host }}:9696',  # noqa
                'openstack endpoint create --region RegionOne network admin http://{{ host.data.controller_host }}:9696',  # noqa
            ),
            env=ADMIN_ENV,
        )


@deploy('Install dashboard service')
def install_dashboard_service(state, host):
    apt.packages(
        {'Install openstack-dashboard'},
        ['openstack-dashboard'],
        latest=True,
    )

    generate_horizon_config = files.template(
        state, host,
        {'Generate horizon config'},
        get_template_path('local_settings.py.j2'),
        '/etc/openstack-dashboard/local_settings.py',
    )

    server.shell(
        state, host,
        {'Give www-data access to the secret key'},
        'chown www-data /var/lib/openstack-dashboard/secret_key',
    )

    init.service(
        state, host,
        {'Restart apache2'},
        'apache2',
        restarted=generate_horizon_config.changed,
    )
