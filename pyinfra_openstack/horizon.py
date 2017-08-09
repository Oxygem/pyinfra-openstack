from pyinfra.api import deploy
from pyinfra.modules import apt, files, init, server

from .util import (
    get_template_path,
)


@deploy('Install dashboard service')
def install_horizon_service(state, host):
    apt.packages(
        {'Install openstack-dashboard'},
        ['openstack-dashboard'],
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
