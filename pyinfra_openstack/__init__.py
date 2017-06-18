# pyinfra-openstack
# File: pyinfra_openstack/__init__.py
# Desc: global imports for pyinfra_openstack module and helper functions

from .controller import install_controller_services
from .glance import install_image_service
from .horizon import install_dashboard_service
from .keystone import install_identity_service
from .neutron import (
    install_dhcp_agent,
    install_linuxbridge_agent,
    install_metadata_agent,
    install_network_node,
    install_network_service,
)
from .nova import install_compute_node, install_compute_service

# Unused
from .chrony import install_chrony_controller, install_chrony_node  # noqa
from .openstack import install_openstack  # noqa


def install_controller(
    identity=True,
    image=True,
    compute=True,
    network=True,
    dashboard=True,
):
    install_controller_services()

    # Install the keystone identity service
    if identity:
        install_identity_service()

    # Install the glance image service
    if image:
        install_image_service()

    # Install the neutron network service
    if network:
        install_network_service()

    # Install the nova compute service
    if compute:
        install_compute_service()

    # Install the horizon dashboard service
    if dashboard:
        install_dashboard_service()


def install_compute():
    '''
    Installs a nova compute node.

    + nova-compute
    '''

    install_compute_node()


def install_network(
    dhcp_agent=True,
    metadata_agent=True,
):
    '''
    Installs a basic network node with the following components (by default):

    + neutron-linuxbridge-agent
    + neutron-dhcp-agent
    + neutron-metadata-agent
    '''

    install_network_node()
    install_linuxbridge_agent()

    if dhcp_agent:
        install_dhcp_agent()

    if metadata_agent:
        install_metadata_agent()

    # TODO: L3 agents
