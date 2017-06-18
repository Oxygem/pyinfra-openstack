from pyinfra.api import deploy
from pyinfra.modules import apt


@deploy('Install OpenStack base')
def install_openstack(state, host):
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
