from pyinfra.api import deploy
from pyinfra.modules import apt, files, init

from .util import get_template_path


@deploy('Install chrony controller')
def install_chrony_controller(state, host):
    apt.packages(
        state, host,
        {'Install chrony'},
        ['chrony'],
    )

    # Chrony
    generate_chrony_config = files.template(
        state, host,
        {'Generate chrony config'},
        get_template_path('chrony-controller.conf.j2'),
        '/etc/chrony/chrony.conf',
    )

    init.service(
        state, host,
        {'Restart chrony'},
        'chrony',
        restarted=generate_chrony_config.changed,
    )


@deploy('Install chrony node')
def install_chrony_node(state, host):
    apt.packages(
        state, host,
        {'Install chrony'},
        ['chrony'],
    )

    generate_chrony_config = files.template(
        state, host,
        {'Generate chrony config'},
        get_template_path('chrony-node.conf.j2'),
        '/etc/chrony/chrony.conf',
    )

    init.service(
        state, host,
        {'Restart chrony'},
        'chrony',
        restarted=generate_chrony_config.changed,
    )
