# pyinfra-openstack
# File: pyinfra_openstack/__init__.py
# Desc: global imports for pyinfra_openstack module and helper functions

from .ceilometer import install_ceilometer_agent, install_ceilometer_service
from .controller import install_controller_services
from .glance import install_glance_service
from .horizon import install_horizon_service
from .keystone import install_keystone_service
from .neutron import (
    install_dhcp_agent,
    install_linuxbridge_agent,
    install_metadata_agent,
    install_neutron_node,
    install_neutron_service,
)
from .nova import install_nova_node, install_nova_service

# Unused
from .chrony import install_chrony_controller, install_chrony_node  # noqa
from .openstack import install_openstack  # noqa


def install_controller(
    # Core OpenStack
    identity=True,
    image=True,
    compute=True,
    network=True,
    # Optional
    dashboard=False,
    telemetry=False,
    placement=False,
):
    install_controller_services()

    # Install the keystone identity service
    if identity:
        install_keystone_service()

    # Install the glance image service
    if image:
        install_glance_service()

    # Install the neutron network service
    if network:
        install_neutron_service(
            nova=compute,
            placement=placement,
        )

    # Install the nova compute service
    if compute:
        install_nova_service(
            neutron=network,
            placement=placement,
        )

    # Install the horizon dashboard service
    if dashboard:
        install_horizon_service()

    # Install the ceilometer telemetry service
    if telemetry:
        install_ceilometer_service()


def install_compute(
    network=True,
    placement=False,
    telemetry=False,
):
    '''
    Installs a nova compute node.

    + nova-compute
    '''

    install_nova_node(
        neutron=network,
        placement=placement,
        ceilometer=telemetry,
    )


def install_network(
    compute=True,
    dhcp_agent=True,
    metadata_agent=True,
):
    '''
    Installs a basic network node with the following components (by default):

    + neutron-linuxbridge-agent
    + neutron-dhcp-agent
    + neutron-metadata-agent
    '''

    install_neutron_node(
        nova=compute,
    )

    install_linuxbridge_agent()

    if dhcp_agent:
        install_dhcp_agent()

    if metadata_agent:
        install_metadata_agent()

    # TODO: L3 agents


def install_telemetry():
    install_ceilometer_agent()
