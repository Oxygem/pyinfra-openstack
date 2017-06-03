from pyinfra.modules import apt, files, init, server

from .controller import (
    install_compute_service,
    install_controller_services,
    install_identity_service,
    install_image_service,
)


def install_base():
    apt.update()
    server.shell(
        'apt-get dist-upgrade -y',
    )

    # Install base apt packages
    apt.packages(
        ['software-properties-common'],
    )

    apt.ppa(
        'cloud-archive:newton',
    )

    apt.update()
    apt.upgrade()

    apt.packages(
        [
            'chrony',
            'python-openstackclient',
        ],
    )


def install_controller():
    # Setup chrony, mysql, rabbitmq, memcached
    install_controller_services()

    # Install the keystone indentity service
    install_identity_service()

    # Install the glance image service
    install_image_service()

    # Install controller compute service
    install_compute_service()


def install_compute():
    files.put(
        'files/chrony-compute.conf',
        '/etc/chrony/chrony.conf',
    )

    init.service(
        'chrony',
        restarted=True,
    )

    apt.packages(
        ['nova-compute'],
    )
