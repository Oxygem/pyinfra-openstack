from pyinfra.modules import apt, files, init, server

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


def install_controller_services():
    files.put(
        'files/chrony-controller.conf',
        '/etc/chrony/chrony.conf',
    )

    init.service(
        'chrony',
        restarted=True,
    )

    apt.packages(
        [
            'mariadb-server',
            'rabbitmq-server',
            'memcached',

            'python-memcache',
            'python-pymysql',
        ],
    )

    files.template(
        'templates/99-openstack.cnf.j2',
        '/etc/mysql/mariadb.conf.d/99-openstack.cnf',
    )

    init.service(
        'mysql',
        restarted=True,
    )

    server.shell((
        'rabbitmqctl add_user openstack 77322d09c192d80e52c78b3228f2ca52a70aa54d || true',
        'rabbitmqctl set_permissions openstack ".*" ".*" ".*"',
    ))

    files.template(
        'templates/memcached.conf.j2',
        '/etc/memcached.conf',
    )

    init.service(
        'memcached',
        restarted=True,
    )


def install_identity_service():
    server.script('scripts/create_database.sh')

    apt.packages(
        ['keystone'],
    )

    files.line(
        '/etc/keystone/keystone.conf',
        'connection=.*',
        replace='connection = mysql+pymysql://keystone:7dc5ddfb1a76ac4935a6d2312baca353ab806895@controller/keystone',  # noqa
    )

    server.shell('keystone-manage db_sync')
    server.script('scripts/keystone_bootstrap.sh')

    files.line(
        '/etc/apache2/apache2.conf',
        'ServerName.*',
        replace='ServerName controller',
    )

    init.service(
        'apache2',
        restarted=True,
    )

    server.shell((
        'openstack project create --domain default service',
        'openstack project create --domain default user',
        'openstack user create --domain default user-1',
        'openstack role create user',
        'openstack role add --project user --user user-1 user',
    ), env=ADMIN_ENV)


def install_image_service():
    server.shell((
        'openstack user create --domain default glance',
        'openstack role add --project service --user glance admin',
        'openstack service create --name glance image',
    ), env=ADMIN_ENV)

    server.shell((
        'openstack endpoint create --region RegionOne image public http://controller:9292',
        'openstack endpoint create --region RegionOne image internal http://controller:9292',
        'openstack endpoint create --region RegionOne image admin http://controller:9292',
    ), env=ADMIN_ENV)

    apt.packages(
        ['glance'],
    )

    files.line(
        '/etc/glance/glance-api.conf',
        'connection=*',
        replace='connection = mysql+pymysql://glance:1c5d384d16e05f70e1d1d0645b95038674b3fa3b@controller/glance',  # noqa
    )

    server.shell('glance-manage db_sync')

    init.service(
        'glance-registry',
        restarted=True,
    )

    init.service(
        'glance-api',
        restarted=True,
    )


def install_compute_service():
    server.shell((
        'openstack user create --domain default nova',
        'openstack role add --project service --user nova admin',
        'openstack service create --name nova compute',
    ), env=ADMIN_ENV)

    server.shell((
        'openstack endpoint create --region RegionOne compute public http://controller:8774/v2.1/%\(tenant_id\)s',  # noqa
        'openstack endpoint create --region RegionOne compute internal http://controller:8774/v2.1/%\(tenant_id\)s',  # noqa
        'openstack endpoint create --region RegionOne compute admin http://controller:8774/v2.1/%\(tenant_id\)s',  # noqa
    ), env=ADMIN_ENV)

    apt.packages([
        'nova-api',
        'nova-conductor',
        'nova-consoleauth',
        'nova-novncproxy',
        'nova-scheduler',
    ])
