from pyinfra.api.deploy import deploy
from pyinfra.modules import apt, files, init, server

from .util import get_template_path


@deploy('Install controller services')
def install_controller_services(state, host):
    apt.packages(
        state, host,
        {'Install packages'},
        [
            'apache2',
            'mariadb-server',
            'rabbitmq-server',
            'memcached',

            'python-memcache',
            'python-pymysql',
        ],
    )

    # MariaDB
    mariadb_configure = files.template(
        state, host,
        {'Generate MariaDB config'},
        get_template_path('mysql.cnf.j2'),
        '/etc/mysql/mariadb.conf.d/99-openstack.cnf',
    )

    init.service(
        state, host,
        {'Restart MariadB'},
        'mysql',
        restarted=mariadb_configure.changed,
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
    memcached_configure = files.template(
        state, host,
        {'Generate memcached config'},
        get_template_path('memcached.conf.j2'),
        '/etc/memcached.conf',
    )

    init.service(
        state, host,
        {'Restart memcached'},
        'memcached',
        restarted=memcached_configure.changed,
    )
