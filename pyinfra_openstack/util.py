from os import path

from pyinfra.modules import server


def get_package_path(*paths):
    return path.join(path.dirname(__file__), *paths)


def get_template_path(filename):
    return get_package_path('templates', filename)


def make_admin_env(host):
    return {
        'OS_PROJECT_DOMAIN_NAME': 'Default',
        'OS_USER_DOMAIN_NAME': 'Default',
        'OS_PROJECT_NAME': 'admin',
        'OS_USERNAME': 'admin',
        'OS_PASSWORD': host.data.admin_password,
        'OS_AUTH_URL': 'http://{0}:35357/v3'.format(host.data.controller_host),
        'OS_IDENTITY_API_VERSION': '3',
        'OS_IMAGE_API_VERSION': '2',
    }


def create_database(state, host, database_name, name=None):
    name = name or database_name

    password = '{{ host.data.%s_password }}' % name

    server.script_template(
        state, host,
        {'Create {0} database'.format(database_name)},
        get_package_path('scripts', 'create_database.sh.j2'),
        database=database_name,
        username=name,
        password=password,
    )


def create_service_user(state, host, name, type_):
    password = '{{ host.data.%s_password }}' % name

    server.shell(
        state, host,
        {'Create {0} {1} user/service'.format(name, type_)},
        (
            'openstack user create --domain default --password {0} {1}'.format(password, name),
            'openstack role add --project service --user {0} admin'.format(name),
            'openstack service create --name {0} {1}'.format(name, type_),
        ),
        env=make_admin_env(host),
    )


def create_service_endpoints(state, host, name, port):
    server.shell(
        state, host,
        {'Create {0} service endpoints'.format(name)},
        (
            'openstack endpoint create --region RegionOne %s public http://{{ host.data.controller_host }}%s' % (name, port),  # noqa
            'openstack endpoint create --region RegionOne %s internal http://{{ host.data.controller_host }}%s' % (name, port),  # noqa
            'openstack endpoint create --region RegionOne %s admin http://{{ host.data.controller_host }}%s' % (name, port),  # noqa
        ),
        env=make_admin_env(host),
    )
