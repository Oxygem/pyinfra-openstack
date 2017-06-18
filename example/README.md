# pyinfra-openstack example

This example uses Vagrant to deploy a local OpenStack cluster, which looks like so:

+ controller
    * keystone (identity)
    * glance (image)
    * horizon (dashboard)
    * nova (compute) controller services
    * neutron (network) server
+ compute_1
    * nova-compute
    * neutron-linuxbridge-agent
    * neutron-dhcp-agent
    * neutron-metadata-agent
+ compute_2
    * nova-compute
    * neutron-linuxbridge-agent
    * neutron-dhcp-agent
    * neutron-metadata-agent
