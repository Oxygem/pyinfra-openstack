from pyinfra import inventory, state

from pyinfra_openstack import (
    install_chrony_controller,
    install_chrony_node,
    install_compute,
    install_controller,
    install_network,
    install_openstack,
)

SUDO = True
FAIL_PERCENT = 0


# Install base repos on all servers
install_openstack()


# Install the controller servers
with state.limit(inventory.get_group('controllers')):
    install_chrony_controller()
    install_controller()


# Install the network/compute servers
with state.limit(inventory.get_group('computes')):
    install_chrony_node()
    install_network()
    install_compute()
