from pyinfra.api import deploy
from pyinfra.modules import apt, files, init, server

from .util import (
    create_database,
    create_service_endpoints,
    create_service_user,
    get_template_path,
)


@deploy('Install network service')
def install_neutron_service(state, host, nova=False, placement=False):
    create_database(state, host, 'neutron')

    neutron_install = apt.packages(
        state, host,
        {'Install neutron network controller packages'},
        [
            'neutron-server',
            'neutron-plugin-ml2',
        ],
    )

    if neutron_install.changed:
        create_service_user(state, host, 'neutron', 'network')
        create_service_endpoints(state, host, 'network', ':9696')

    neutron_configure = files.template(
        state, host,
        {'Generate neutron config'},
        get_template_path('neutron-controller.conf.j2'),
        '/etc/neutron/neutron.conf',
        nova=nova,
    )

    ml2_plugin_configure = files.template(
        state, host,
        {'Generate neutron ml2 plugin config'},
        get_template_path('ml2_conf.ini.j2'),
        '/etc/neutron/plugins/ml2/ml2_conf.ini',
    )

    server.shell(
        {'Sync the neutron database'},
        '''
        neutron-db-manage --config-file /etc/neutron/neutron.conf \
            --config-file /etc/neutron/plugins/ml2/ml2_conf.ini \
            upgrade head
        ''',
    )

    init.service(
        state, host,
        {'Restart neutron-server'},
        'neutron-server',
        restarted=neutron_configure.changed or ml2_plugin_configure.changed,
    )


def _install_agent(state, host, agent_name, template_name, config_path):
    install = apt.packages(
        state, host,
        {'Install {0} package'.format(agent_name)},
        [agent_name],
    )

    configure = files.template(
        state, host,
        {'Generate neutron {0} agent config'.format(agent_name)},
        get_template_path(template_name),
        config_path,
    )

    init.service(
        state, host,
        {'Restart {0}'.format(agent_name)},
        agent_name,
        restarted=install.changed or configure.changed,
    )


@deploy('Install network node config')
def install_neutron_node(state, host, nova=False):
    files.directory(
        {'Create neutron config directory'},
        '/etc/neutron',
    )

    files.template(
        state, host,
        {'Generate neutron config'},
        get_template_path('neutron-node.conf.j2'),
        '/etc/neutron/neutron.conf',
        nova=nova,
    )


@deploy('Install linuxbridge agent')
def install_linuxbridge_agent(state, host):
    _install_agent(
        state, host,
        'neutron-linuxbridge-agent',
        'linuxbridge_agent.ini.j2',
        '/etc/neutron/plugins/ml2/linuxbridge_agent.ini',
    )


@deploy('Install dhcp agent')
def install_dhcp_agent(state, host):
    _install_agent(
        state, host,
        'neutron-dhcp-agent',
        'dhcp_agent.ini.j2',
        '/etc/neutron/dhcp_agent.ini',
    )


@deploy('Install metadata agent')
def install_metadata_agent(state, host):
    _install_agent(
        state, host,
        'neutron-metadata-agent',
        'metadata_agent.ini.j2',
        '/etc/neutron/metadata_agent.ini',
    )
