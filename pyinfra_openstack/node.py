from pyinfra.api.deploy import deploy
from pyinfra.modules import apt, files, init

from .util import get_template_path


@deploy('Install node services')
def install_node_services(state, host):
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


@deploy('Install compute node')
def install_compute_node(state, host):
    apt.packages(
        state, host,
        {'Install nova-compute'},
        ['nova-compute'],
    )

    generate_nova_config = files.template(
        state, host,
        {'Generate nova config'},
        get_template_path('nova-node.conf.j2'),
        '/etc/nova/nova.conf',
    )

    init.service(
        state, host,
        {'Restart nova-compute'},
        'nova-compute',
        restarted=generate_nova_config.changed,
    )
