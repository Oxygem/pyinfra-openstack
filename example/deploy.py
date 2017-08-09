from pyinfra import inventory, state

from pyinfra_openstack import (
    install_chrony_controller,
    install_chrony_node,
    install_compute,
    install_controller,
    install_network,
    install_openstack,
    install_telemetry,
)

SUDO = True
FAIL_PERCENT = 0


# Install base repos on all servers
install_openstack()


# Install the controller servers
with state.limit(inventory.get_group('controllers')):
    install_chrony_controller()
    install_controller(
        dashboard=True,
        telemetry=True,
        placement=True,
    )


# Install the network/compute servers
with state.limit(inventory.get_group('computes')):
    install_chrony_node()
    install_network()
    install_telemetry()
    install_compute(
        placement=True,
        telemetry=True,
    )
