from pyinfra.api.deploy import deploy
from pyinfra.modules import apt, files, init, server

from .util import (
    create_database,
    create_service_endpoints,
    create_service_user,
    get_template_path,
)


@deploy('Install image service')
def install_image_service(state, host):
    install_glance = apt.packages(
        state, host,
        {'Install glance'},
        ['glance'],
    )

    if install_glance.changed:
        create_database(state, host, 'glance')
        create_service_user(state, host, 'glance', 'image')
        create_service_endpoints(state, host, 'image', ':9292')

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
