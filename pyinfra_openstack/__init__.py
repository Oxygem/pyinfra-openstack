from pyinfra.api.deploy import deploy
from pyinfra.modules import apt

from .controller import (
    install_compute_service,
    install_controller_services,
    install_dashboard_service,
    install_identity_service,
    install_image_service,
)
from .node import (
    install_compute_node,
    install_node_services,
)


@deploy('Install OpenStack base')
def install_base(state, host):
    # Install base apt packages
    apt.packages(
        state, host,
        {'Install software-properties-common'},
        ['software-properties-common'],
        update=True,
        cache_time=3600,
    )

    add_ppa = apt.ppa(
        state, host,
        {'Add the OpenStack PPA'},
        'cloud-archive:ocata',
    )

    if add_ppa.changed:
        apt.update(
            state, host,
            {'Update apt'},
        )

    apt.upgrade(
        state, host,
        {'Upgrade apt packages'},
    )

    apt.packages(
        state, host,
        {'Install python-openstackclient'},
        ['python-openstackclient'],
        latest=True,
    )


def install_controller(
    identity=True,
    image=True,
    compute=True,
    dashboard=True,
):
    install_controller_services()

    # Install the keystone identity service (required)
    if identity:
        install_identity_service()

    # Install the glance image service
    if image:
        install_image_service()

    # Install the nova compute service
    if compute:
        install_compute_service()

    # Install the horizon dashboard service
    if dashboard:
        install_dashboard_service()


def install_compute():
    install_node_services()

    # Install the nova compute node
    install_compute_node()
