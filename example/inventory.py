from os import environ, path


def make_hosts(*name_ips):
    hosts = []

    for name, ip in name_ips:
        vagrant_name = name.replace('-', '_')

        private_key_file = path.join(
            environ.get('VAGRANT_DOTFILE_PATH', '.vagrant'),
            'machines',
            vagrant_name,
            'virtualbox',
            'private_key',
        )

        hosts.append(
            (name, {
                'ssh_hostname': ip,
                'ssh_user': 'ubuntu',
                'ssh_key': private_key_file,
            }),
        )

    return hosts


controllers = make_hosts(
    ('controller', '10.40.40.40'),
)

computes = make_hosts(
    ('compute-1', '10.40.40.41'),
    ('compute-2', '10.40.40.42'),
)
