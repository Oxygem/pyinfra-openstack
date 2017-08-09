from pyinfra.api.deploy import deploy
from pyinfra.modules import apt, files, init

from .util import (
    create_service_endpoints,
    create_service_user,
    get_template_path,
)


@deploy('Install telemetry service')
def install_ceilometer_service(state, host):
    ceilometer_install = apt.packages(
        state, host,
        {'Install ceilometer controller packages'},
        [
            'ceilometer-collector',
            'ceilometer-agent-central',
            'ceilometer-agent-notification',
            'python-ceilometerclient',
        ],
    )

    if ceilometer_install.changed:
        create_service_user(state, host, 'ceilometer', 'metering')

        create_service_user(state, host, 'gnocchi', 'metric')
        create_service_endpoints(state, host, 'metric', ':8041')

    ceilometer_configure = files.template(
        state, host,
        {'Generate ceilometer config'},
        get_template_path('ceilometer-controller.conf.j2'),
        '/etc/ceilometer/ceilometer.conf',
    )

    # server.shell(
    #     state, host,
    #     {'Create ceilometer resoucres in gnocchi'},
    #     'ceilometer-upgrade --skip-metering-database',
    # )

    for service in (
        'ceilometer-agent-central',
        'ceilometer-agent-notification',
        'ceilometer-collector',
    ):
        init.service(
            state, host,
            {'Restart {0}'.format(service)},
            service,
            restarted=ceilometer_configure,
        )


@deploy('Install telemetry agent')
def install_ceilometer_agent(state, host):
    apt.packages(
        {'Install ceilometer-agent-compute'},
        'ceilometer-agent-compute',
    )

    ceilometer_configure = files.template(
        state, host,
        {'Generate ceilometer config'},
        get_template_path('ceilometer-node.conf.j2'),
        '/etc/ceilometer/ceilometer.conf',
    )

    init.service(
        state, host,
        {'Restart ceilometer-agent-compute'},
        'ceilometer-agent-compute',
        restarted=ceilometer_configure.changed,
    )
