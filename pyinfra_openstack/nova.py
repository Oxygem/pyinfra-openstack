from pyinfra.api import deploy
from pyinfra.modules import apt, files, init, server

from .util import (
    create_database,
    create_service_endpoints,
    create_service_user,
    get_template_path,
)


@deploy('Install compute service')
def install_compute_service(state, host):
    create_database(state, host, 'nova')
    create_database(state, host, 'nova_api', name='nova')
    create_database(state, host, 'nova_cell0', name='nova')

    nova_install = apt.packages(
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
    )

    if nova_install.changed:
        create_service_user(state, host, 'nova', 'compute')
        create_service_endpoints(state, host, 'compute', ':8774/v2.1/%\(tenant_id\)s')

        create_service_user(state, host, 'placement', 'placement')
        create_service_endpoints(state, host, 'placement', ':8778')

    nova_configure = files.template(
        state, host,
        {'Generate nova config'},
        get_template_path('nova-controller.conf.j2'),
        '/etc/nova/nova.conf',
    )

    server.shell(
        state, host,
        {'Sync the nova api database'},
        'nova-manage api_db sync',
    )

    if nova_install.changed:
        server.shell(
            state, host,
            {'Setup nova cells and sync db'},
            (
                'nova-manage cell_v2 map_cell0',
                'nova-manage cell_v2 create_cell --name=cell1 --verbose',
            ),
        )

    server.shell(
        state, host,
        {'Sync the nova database'},
        'nova-manage db sync',
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
            restarted=nova_configure.changed,
        )


@deploy('Install compute node')
def install_compute_node(state, host):
    apt.packages(
        state, host,
        {'Install nova-compute'},
        ['nova-compute'],
    )

    files.put(
        {'Upload interface.j2'},
        get_template_path('interfaces.j2'),
        '/etc/nova/interfaces.j2',
    )

    nova_configure = files.template(
        state, host,
        {'Generate nova config'},
        get_template_path('nova-node.conf.j2'),
        '/etc/nova/nova.conf',
    )

    nova_compute_configure = files.template(
        state, host,
        {'Generate nova-compute config'},
        get_template_path('nova-compute.conf.j2'),
        '/etc/nova/nova-compute.conf',
    )

    init.service(
        state, host,
        {'Restart nova-compute'},
        'nova-compute',
        restarted=nova_configure.changed or nova_compute_configure.changed,
    )
