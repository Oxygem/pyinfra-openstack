# pyinfra-openstack

[pyinfra](https://github.com/Fizzadar/pyinfra) deploys for setting up an OpenStack cluster.

This is a work in progress...


## Quickstart

```sh
# Install pyinfra_openstack (& pyinfra if needed)
pip install pyinfra_openstack

# Create an inventory
nano inventory.py
```

```py
# inventory.py
controllers = ['192.168.0.1']
computes = ['192.168.0.2', '192.168.0.3']
```

```sh
# Create a deploy
nano deploy.py
```

```py
# inventory.py
from pyinfra import inventory, state

from pyinfra_openstack import (
    install_base,
    install_compute_node,
    install_compute_service,
    install_controller_services,
    install_identity_service,
    install_image_service,
    install_node_services,
)

SUDO = True
FAIL_PERCENT = 0


# Install base repos on all servers
install_base()


# Install the controller servers
with state.limit(inventory.get_group('controllers')):
    install_controller_services()

    # Install the keystone identity service (required)
    install_identity_service()

    # Install the glance image service
    install_image_service()

    # Install the nova compute service
    install_compute_service()


# Install the compute servers
with state.limit(inventory.get_group('computes')):
    install_node_services()

    # Install the nova compute node
    install_compute_node()
```

```sh
# Run pyinfra
pyinfra inventory.py deploy.py
```
