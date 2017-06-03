from pyinfra import inventory, state

from pyinfra_openstack import (
    install_base,
    install_compute,
    install_controller,
)

SUDO = True
FAIL_PERCENT = 0


# Install base repos on all servers
install_base()


# Install the controller servers
state.limit_hosts = inventory.get_group('controllers')
install_controller()


# Install the compute servers
state.limit_hosts = inventory.get_group('computes')
install_compute()
