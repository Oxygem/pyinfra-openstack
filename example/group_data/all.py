from pyinfra import inventory


admin_password = 'a5db2a4d0d0b8f04668f3900e4ceddf7f60ef80a'

rabbitmq_password = '77322d09c192d80e52c78b3228f2ca52a70aa54d'
keystone_password = '7dc5ddfb1a76ac4935a6d2312baca353ab806895'
glance_password = '1c5d384d16e05f70e1d1d0645b95038674b3fa3b'
nova_password = 'ce5ddb82e7679baaaaf9dc2d05e4f920e4cc73a4'
placement_password = 'aff05a8f2415df8322a90847bb2ee8b0bb07c650'
neutron_password = '1e15bb483a2b2acb8d52b58db3686e02b7d45676'

metadata_secret = '01c61cc7aa38e2a96b8f3e9bb55a813fe78815b7'

virt_type = 'qemu'

bridge_interface = 'enp0s9'

# The controllers group only contains one host
controller_host = inventory.get_group('controllers')[0].data.ssh_hostname
